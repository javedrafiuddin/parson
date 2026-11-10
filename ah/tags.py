"""XBRL concepts extracted into the point-in-time FILINGS-facts table. Grouped by the feature they feed."""
DEI = ["EntityCommonStockSharesOutstanding", "EntityPublicFloat"]
REVENUE = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
           "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "SalesRevenueGoodsNet",
           "SalesRevenueServicesNet", "RevenuesNetOfInterestExpense", "RevenueMineralSales",
           "ContractsRevenue", "HealthCareOrganizationRevenue", "OilAndGasRevenue", "RealEstateRevenueNet"]
CASH = ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        "CashCashEquivalentsAndShortTermInvestments", "Cash", "ShortTermInvestments", "MarketableSecuritiesCurrent",
        "AvailableForSaleSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
        "DebtSecuritiesAvailableForSaleCurrent" if False else "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
        "CashAndCashEquivalentsPeriodIncreaseDecrease"]
DEBT = ["LongTermDebt", "LongTermDebtNoncurrent", "LongTermDebtCurrent", "DebtCurrent", "ShortTermBorrowings",
        "ConvertibleNotesPayable", "ConvertibleNotesPayableCurrent", "ConvertibleNotesPayableNoncurrent",
        "ConvertibleDebtNoncurrent", "ConvertibleDebtCurrent", "ConvertibleDebt", "NotesPayable",
        "NotesPayableCurrent", "LongTermNotesPayable", "LongTermDebtAndCapitalLeaseObligations",
        "LongTermDebtAndCapitalLeaseObligationsCurrent", "DebtLongtermAndShorttermCombinedAmount", "LineOfCredit",
        "SeniorNotes", "SecuredDebt", "DebtInstrumentCarryingAmount",
        "LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths", "NotesPayableRelatedPartiesClassifiedCurrent"]
CASHFLOW = ["NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
            "NetCashProvidedByUsedInFinancingActivities", "NetCashProvidedByUsedInInvestingActivities",
            "ProceedsFromIssuanceOfCommonStock", "ProceedsFromIssuanceOrSaleOfEquity",
            "ProceedsFromIssuanceOfPrivatePlacement", "ProceedsFromConvertibleNotesPayable",
            "ProceedsFromWarrantExercises", "PaymentsToAcquirePropertyPlantAndEquipment"]
BALANCE = ["Assets", "AssetsCurrent", "Liabilities", "LiabilitiesCurrent", "StockholdersEquity",
           "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
           "AssetsHeldInTrustNoncurrent", "AssetsHeldInTrust", "Goodwill", "PropertyPlantAndEquipmentNet"]
INCOME = ["NetIncomeLoss", "ProfitLoss", "OperatingIncomeLoss", "GrossProfit", "ResearchAndDevelopmentExpense",
          "CostOfRevenue", "InterestExpense"]
SHARES = ["CommonStockSharesOutstanding", "CommonStockSharesIssued", "CommonStockSharesAuthorized",
          "WeightedAverageNumberOfSharesOutstandingBasic", "WeightedAverageNumberOfDilutedSharesOutstanding",
          "StockIssuedDuringPeriodSharesNewIssues", "StockholdersEquityNoteStockSplitConversionRatio1"]
DILUTIVE = ["ClassOfWarrantOrRightOutstanding", "ClassOfWarrantOrRightExercisePriceOfWarrantsOrRights1",
            "ClassOfWarrantOrRightNumberOfSecuritiesCalledByWarrantsOrRights",
            "ShareBasedCompensationArrangementByShareBasedPaymentAwardOptionsOutstandingNumber",
            "ShareBasedCompensationArrangementByShareBasedPaymentAwardEquityInstrumentsOtherThanOptionsNonvestedNumber",
            "ShareBasedCompensationArrangementByShareBasedPaymentAwardNumberOfSharesAvailableForGrant",
            "AntidilutiveSecuritiesExcludedFromComputationOfEarningsPerShareAmount",
            "DebtInstrumentConvertibleConversionPrice1", "PreferredStockLiquidationPreferenceValue",
            "PreferredStockValue", "TemporaryEquityCarryingAmountAttributableToParent",
            "PreferredStockSharesOutstanding", "TemporaryEquitySharesOutstanding",
            "WarrantsAndRightsOutstanding", "DerivativeLiabilities", "WarrantsAndRightsOutstandingTerm"]
USGAAP = sorted(set(REVENUE + CASH + DEBT + CASHFLOW + BALANCE + INCOME + SHARES + DILUTIVE))
ALL = {"dei": DEI, "us-gaap": USGAAP}
