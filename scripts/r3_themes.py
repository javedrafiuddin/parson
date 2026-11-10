"""Emergent theme clusters (Section 4 'fallen leaders, discovered not assumed'). No hand-written theme list:
TF-IDF + NMF topics over company descriptions of ALL Stage-1 survivors; topic labels are the top terms themselves.
Fallen leader = within a topic, a name down >= 60% whose 3-year-high market cap ranked in the topic's top quartile.
Writes data/derived/themes.parquet (+ topic term table) and prints the cluster table for screen_log.md."""
import sys, pathlib, json, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.decomposition import NMF
from ah.config import DERIVED

K = int(sys.argv[1]) if len(sys.argv) > 1 else 45
pr = pd.read_parquet(DERIVED / "profiles.parquet").dropna(subset=["description"]).drop_duplicates("cik")
sc = pd.read_parquet(DERIVED / "baserate_scores.parquet")
d = sc.merge(pr[["cik", "description"]], on="cik", how="inner")
stop = list(ENGLISH_STOP_WORDS | set("company companies inc corp corporation holdings founded headquartered based products product services service solutions provides provide offers offer operates operate segments segment including include also business through its their well various united states customers customer new york california texas name formerly known changed subsidiaries subsidiary develops development develop engaged primarily markets market sells sell sale north america american international global worldwide llc ltd group co incorporated related use used using designed designs range addition approximately brand brands under names across industry industries".split()))
tv = TfidfVectorizer(stop_words=stop, ngram_range=(1, 2), min_df=4, max_df=0.25, sublinear_tf=True, token_pattern=r"[a-zA-Z][a-zA-Z\-]{2,}")
X = tv.fit_transform(d.description.str.lower())
nmf = NMF(n_components=K, init="nndsvd", random_state=0, max_iter=600)
W = nmf.fit_transform(X)
terms = np.array(tv.get_feature_names_out())
top = [", ".join(terms[np.argsort(-nmf.components_[k])[:7]]) for k in range(K)]
d["topic"] = W.argmax(axis=1)
d["topic_strength"] = W.max(axis=1) / (W.sum(axis=1) + 1e-12)
d["topic_terms"] = d.topic.map(dict(enumerate(top)))
d["peak_mcap"] = d.mcap / (1 - d.dd.clip(upper=0.995))
rows = []
for k, g in d.groupby("topic"):
    dm = g[g.dd >= 0.6]
    q = g.peak_mcap.quantile(0.75)
    fl = dm[dm.peak_mcap >= q].sort_values("peak_mcap", ascending=False)
    rows.append({"topic": k, "terms": top[k], "n": len(g), "n_dd60": len(dm), "n_dd80": int((g.dd >= 0.8).sum()), "share_dd60": round(len(dm) / len(g), 2),
                 "median_dd": round(float(g.dd.median()), 2), "fallen_leaders": ", ".join(fl.symbol.head(6)), "n_fallen_leaders": len(fl)})
T = pd.DataFrame(rows).sort_values("n_dd60", ascending=False)
d["fallen_leader"] = False
for k, g in d.groupby("topic"):
    q = g.peak_mcap.quantile(0.75)
    d.loc[g[(g.dd >= 0.6) & (g.peak_mcap >= q)].index, "fallen_leader"] = True
d[["cik", "symbol", "topic", "topic_terms", "topic_strength", "fallen_leader", "peak_mcap", "description"]].to_parquet(DERIVED / "themes.parquet", index=False)
T.to_csv(DERIVED / "theme_clusters.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 95); pd.set_option("display.max_rows", 100)
print(T[["topic", "terms", "n", "n_dd60", "n_dd80", "median_dd", "fallen_leaders"]].to_string())
