# 990 XML Narrative Field Inventory (Phase 1)

Generated from IRS batch `2026_TEOS_XML_06A` (24 sampled filings across ['990', '990EZ', '990PF']).
Raw XML samples: `data/990_xml/samples/`. Manifest (EIN/form/NTEE1/mission_source
per sample): `data/990_xml/samples/manifest.csv`. Regenerate with
`python3 -m scripts.enrichment.narrative_990.inventory_xml_fields`.

Programmatic walk of every sampled filing's full XML tree. A row here means the element appeared with non-trivial text in at least one sampled filing. Not every field below is useful to Daanaa; the summary here calls out which ones are, deferring the rest.

## Summary — narrative fields worth extracting

| Field | Form | Status today | Verdict |
|---|---|---|---|
| `IRS990/ActivityOrMissionDesc` | 990 | **Extracted** (`parse_990_xml`, Part I mission) | Keep as primary mission source. |
| `IRS990/MissionDesc` | 990 | **Not extracted** — distinct from `ActivityOrMissionDesc`, sits inside the Part III accomplishments block, present in every 990 sampled (8/8) | New: check as a second mission candidate ahead of the Part III accomplishment-join fallback — it reads as the org's own longer mission statement, not a program description. |
| `IRS990/Desc` (`ProgramServiceAccomplishmentGrp/DescriptionProgramServiceAccomTxt`) | 990 | **Extracted, but only as mission fallback** (joined together, not stored individually) | New: store each Part III item as its own program record (name/expense/description), not just concatenated into `mission`. |
| `IRS990EZ/PrimaryExemptPurposeTxt` | 990EZ | Not extracted | New: 990-EZ's mission-equivalent field. `fetch_irs_direct_filing.py` only processes `RETURN_TYPE == '990'` today — 990-EZ needs its own code path. |
| `IRS990EZ/ProgramSrvcAccomplishmentGrp/DescriptionProgramSrvcAccomTxt` | 990EZ | Not extracted | New: 990-EZ's Part III equivalent. |
| `IRS990ScheduleO/SupplementalInformationDetail/ExplanationTxt` (+ `FormAndLineReferenceDesc`) | 990, 990EZ | Not extracted (the `extracted_programs` table was designed for this and left empty) | New, high value: appeared 44 times across 8 sampled 990s (avg 5.5/filing), 23 times across 8 sampled 990-EZs. Longest single snippet: 5,664 chars. `FormAndLineReferenceDesc` tells you which Part/Line each explanation is answering — needed to filter to the useful ones (mission/program-adjacent lines) vs. boilerplate (e.g. governance policy explanations). |
| `IRS990ScheduleF/GrantsToOrgOutsideUSGrp/PurposeOfGrantTxt` + `RegionTxt` | 990 | Not extracted | New: foreign grant purpose + geography — directly answers "grantmaking purposes" and "geographic areas served" for grantmaking orgs. |
| `IRS990ScheduleI/RecipientTable/PurposeOfGrantTxt` | 990 | Not extracted | New: domestic grant purpose. Short (often <20 chars, e.g. "CONSERVE WILDLIFE") — useful but needs the junk filter (see below). |
| `IRS990PF/SupplementaryInformationGrp/GrantOrContributionPdDurYrGrp/GrantOrContributionPurposeTxt` | 990PF | Not extracted | New, but **noisy**: in the sample, most values were literally `"SEE ATTACHED"` (25 occurrences, junk) rather than an actual purpose. Needs the same `JUNK` filter convention as `ingest_990_missions.py` before this is usable signal. |
| `IRS990PF/.../RecipientBusinessName` / `RecipientPersonNm` + address | 990PF | Not extracted | For grantmaking foundations, this is who they fund — useful context but is *about the recipient*, not the filer; needs a different presentation (not "what this org does" but "who this org funds") to avoid misattributing recipient info as the filer's own activity. |
| `IRS990ScheduleR/.../ExplanationTxt` | 990 | Not extracted | Mixed value — one sample instance was literally a restated mission ("OUR MISSION IS TO SHIFT POWER..."), but Schedule R is about related-org transactions, so most instances will be transaction explanations, not narrative. Low priority. |

Every other row in the full tables below is a person name, address, dollar
amount, or boilerplate declaration (e.g. `ReasonableCauseExplanation` for a
late filing) — not narrative Daanaa should surface. Full raw walk retained
below for reference / future re-mining.

## 990 (8 sampled filings)

| Path | Seen in N filings | Max text len | Example snippet |
|---|---|---|---|
| `/Return/ReturnData/IRS990ScheduleO/SupplementalInformationDetail/ExplanationTxt` | 44 | 5664 | ART IN THE WILD & OTHER ANNUAL EVENTS IN OCTOBER, ART IN THE WILD CELEBRATES NATIONAL WILDLIFE REFUGE WEEK, THE BIRTHDAY OF THE REFUGE'S NAMESAKE, JAY NORWOOD " |
| `/Return/ReturnData/IRS990ScheduleO/SupplementalInformationDetail/FormAndLineReferenceDesc` | 39 | 38 | FORM 990, PART VI, SECTION B, LINE 11B |
| `/Return/ReturnData/IRS990/OtherExpensesGrp/ProgramServicesAmt` | 23 | 6 | 696404 |
| `/Return/ReturnData/IRS990/Form990PartVIISectionAGrp/PersonNm` | 19 | 23 | IRIS SHVARTZMAN SHLOMOF |
| `/Return/ReturnData/IRS990/OtherExpensesGrp/Desc` | 18 | 26 | Intervention and Education |
| `/Return/ReturnHeader/ReturnTs` | 8 | 25 | 2026-06-15T20:44:30-05:00 |
| `/Return/ReturnHeader/PreparerFirmGrp/PreparerUSAddress/AddressLine1Txt` | 8 | 33 | ONE SANSOME STREET SUITE 3500 PMB |
| `/Return/ReturnHeader/Filer/USAddress/AddressLine1Txt` | 8 | 24 | 20935 WARNER CENTER LN B |
| `/Return/ReturnHeader/BuildTS` | 8 | 20 | 2025-03-06 01:10:19Z |
| `/Return/ReturnData/IRS990/ActivityOrMissionDesc` | 8 | 277 | TO EDUCATE ENERGY PROFESSIONALS ACROSS ALL ENERGY SECTORS WHO ARE COMMITTED TO THE BALANCING OF FOSSIL AND RENEWABLE ENERGY AND IMPLEMENTING COMPREHENSIVE ENERG |
| `/Return/ReturnData/IRS990/CYProgramServiceRevenueAmt` | 8 | 6 | 394037 |
| `/Return/ReturnData/IRS990/MissionDesc` | 8 | 741 | "FOUNDED IN 1945, THE J.N. "DING" DARLING NATIONAL WILDLIFE REFUGE CONSISTS OF NEARLY 8,000 ACRES OF SOME OF THE MOST UNIQUE AND ECOLOGICALLY IMPORTANT ECOSYSTE |
| `/Return/ReturnData/IRS990/Desc` | 8 | 5664 | ART IN THE WILD & OTHER ANNUAL EVENTS IN OCTOBER, ART IN THE WILD CELEBRATES NATIONAL WILDLIFE REFUGE WEEK, THE BIRTHDAY OF THE REFUGE'S NAMESAKE, JAY NORWOOD " |
| `/Return/ReturnData/IRS990/TotalProgramServiceExpensesAmt` | 8 | 7 | 1759602 |
| `/Return/ReturnData/IRS990/TotalFunctionalExpensesGrp/ProgramServicesAmt` | 8 | 7 | 1759602 |
| `/Return/ReturnData/IRS990/BooksInCareOfDetail/USAddress/AddressLine1Txt` | 7 | 24 | 20935 WARNER CENTER LN B |
| `/Return/ReturnData/IRS990/FeesForServicesOtherGrp/ProgramServicesAmt` | 7 | 6 | 243720 |
| `/Return/ReturnHeader/Filer/BusinessName/BusinessNameLine1Txt` | 7 | 33 | DING DARLING WILDLIFE SOCIETY INC |
| `/Return/ReturnHeader/PreparerFirmGrp/PreparerFirmName/BusinessNameLine1Txt` | 6 | 29 | THOMSON BROCK LUGER & COMPANY |
| `/Return/ReturnData/IRS990/USAddress/AddressLine1Txt` | 6 | 24 | 20935 WARNER CENTER LN B |
| `/Return/ReturnData/IRS990/TotalProgramServiceRevenueAmt` | 6 | 6 | 394037 |
| `/Return/ReturnData/IRS990/TravelGrp/ProgramServicesAmt` | 6 | 5 | 35510 |
| `/Return/ReturnData/IRS990/InsuranceGrp/ProgramServicesAmt` | 6 | 5 | 11152 |
| `/Return/ReturnHeader/PreparerPersonGrp/PreparerPersonNm` | 5 | 26 | ISAGANI FERDINAND LAGUISMA |
| `/Return/ReturnData/IRS990/PYProgramServiceRevenueAmt` | 5 | 6 | 409064 |
| `/Return/ReturnData/IRS990/Form990PartVIISectionAGrp/TitleTxt` | 5 | 24 | VICE PRESIDENT/TREASURER |
| `/Return/ReturnData/IRS990/ProgramServiceRevenueGrp/Desc` | 5 | 25 | REGISTRATIONS - EDUCATION |
| `/Return/ReturnData/IRS990/InformationTechnologyGrp/ProgramServicesAmt` | 5 | 6 | 195054 |
| `/Return/ReturnData/IRS990/ConferencesMeetingsGrp/ProgramServicesAmt` | 5 | 6 | 223994 |
| `/Return/ReturnHeader/BusinessOfficerGrp/PersonNm` | 5 | 19 | ANN MARIE E WILDMAN |
| `/Return/ReturnData/IRS990/OccupancyGrp/ProgramServicesAmt` | 5 | 5 | 38650 |
| `/Return/ReturnData/IRS990/DepreciationDepletionGrp/ProgramServicesAmt` | 5 | 6 | 113914 |
| `/Return/ReturnHeader/BusinessOfficerGrp/PersonTitleTxt` | 4 | 23 | CHIEF EXECUTIVE OFFICER |
| `/Return/ReturnData/IRS990/WebsiteAddressTxt` | 4 | 26 | HTTPS://EFBCCONFERENCE.ORG |
| `/Return/ReturnData/IRS990/CompCurrentOfcrDirectorsGrp/ProgramServicesAmt` | 4 | 6 | 120993 |
| `/Return/ReturnData/IRS990/OtherEmployeeBenefitsGrp/ProgramServicesAmt` | 4 | 5 | 19116 |
| `/Return/ReturnData/IRS990/PayrollTaxesGrp/ProgramServicesAmt` | 4 | 5 | 32590 |
| `/Return/ReturnData/IRS990/FeesForServicesAccountingGrp/ProgramServicesAmt` | 4 | 5 | 19791 |
| `/Return/ReturnData/IRS990ScheduleF/AccountActivitiesOutsideUSGrp/TypeOfActivitiesConductedTxt` | 4 | 38 | GRANTS TO RECIPIENTS LOCATED IN REGION |
| `/Return/ReturnData/IRS990/AllOtherExpensesGrp/ProgramServicesAmt` | 4 | 5 | 58783 |
| `/Return/ReturnData/IRS990/PrincipalOfficerNm` | 4 | 19 | ANN MARIE E WILDMAN |
| `/Return/ReturnData/IRS990ScheduleI/RecipientTable/RecipientBusinessName/BusinessNameLine1Txt` | 4 | 30 | BAILEY-MATTHEWS NATIONAL SHELL |
| `/Return/ReturnData/IRS990/OtherSalariesAndWagesGrp/ProgramServicesAmt` | 3 | 6 | 285685 |
| `/Return/ReturnData/IRS990/AdvertisingGrp/ProgramServicesAmt` | 3 | 4 | 7072 |
| `/Return/ReturnData/IRS990/OfficeExpensesGrp/ProgramServicesAmt` | 3 | 5 | 47924 |
| `/Return/ReturnData/IRS990ScheduleF/AccountActivitiesOutsideUSGrp/RegionTxt` | 3 | 33 | CENTRAL AMERICA AND THE CARIBBEAN |
| `/Return/ReturnData/IRS990ScheduleF/GrantsToOrgOutsideUSGrp/PurposeOfGrantTxt` | 3 | 55 | TO SUPPORT MISSION IN CENTRAL AMERICA AND THE CARIBBEAN |
| `/Return/ReturnData/IRS990ScheduleD/SupplementalInformationDetail/FormAndLineReferenceDesc` | 3 | 37 | SCHEDULE D, PAGE 4, PART XII, LINE 2D |
| `/Return/ReturnData/IRS990ScheduleD/SupplementalInformationDetail/ExplanationTxt` | 3 | 1246 | THE INTERNAL REVENUE SERVICE HAS DETERMINED THAT THE ORGANIZATION IS EXEMPT FROM FEDERAL INCOME TAXES UNDER SECTION 501(C)3 OF THE INTERNAL REVENUE CODE. THE OR |
| `/Return/ReturnData/IRS990ScheduleI/RecipientTable/USAddress/AddressLine1Txt` | 3 | 24 | 1701 K STREET NW STE 550 |
| `/Return/ReturnData/IRS990ScheduleI/RecipientTable/PurposeOfGrantTxt` | 3 | 17 | CONSERVE WILDLIFE |
| `/Return/ReturnData/IRS990/ContractorCompensationGrp/ContractorAddress/USAddress/AddressLine1Txt` | 3 | 22 | 3702 Spectrum Blvd 165 |
| `/Return/ReturnData/IRS990/ContractorCompensationGrp/ServicesDesc` | 3 | 45 | Organization operations & management services |
| `/Return/ReturnData/IRS990ScheduleD/OtherLiabilitiesOrgGrp/Desc` | 2 | 33 | CITY OF VALENTINE BLDG GRANT/LOAN |
| `/Return/ReturnData/IRS990ScheduleF/GrantsToOrgOutsideUSGrp/RegionTxt` | 2 | 33 | CENTRAL AMERICA AND THE CARIBBEAN |
| `/Return/ReturnData/IRS990ScheduleR/TransactionsRelatedOrgGrp/OtherOrganizationName/BusinessNameLine1Txt` | 2 | 24 | WEROBOTICS (SWITZERLAND) |
| `/Return/ReturnData/IRS990ScheduleR/TransactionsRelatedOrgGrp/MethodOfAmountDeterminationTxt` | 2 | 23 | ACTUAL AMOUNT DISBURSED |
| `/Return/ReturnData/IRS990ScheduleL/BusTrInvolveInterestedPrsnGrp/RelationshipDescriptionTxt` | 2 | 25 | Owned by ED Jennifer Webb |
| `/Return/ReturnData/IRS990ScheduleL/BusTrInvolveInterestedPrsnGrp/TransactionDesc` | 2 | 45 | Organization operations & management services |
| `/Return/ReturnData/IRS990ScheduleA/Form990ScheduleAPartVIGrp/FormAndLineReferenceDesc` | 2 | 19 | SUPPORTING SCHEDULE |
| `/Return/ReturnData/IRS990/ContractorCompensationGrp/ContractorName/PersonNm` | 2 | 35 | Pinellas Ex-Offender Re-Entry Coali |
| `/Return/ReturnData/IRS990/ForeignGrantsGrp/ProgramServicesAmt` | 1 | 6 | 181071 |
| `/Return/ReturnData/IRS990ScheduleF/SupplementalInformationDetail/FormAndLineReferenceDesc` | 1 | 15 | PART I, LINE 2: |
| `/Return/ReturnData/IRS990ScheduleF/SupplementalInformationDetail/ExplanationTxt` | 1 | 154 | GRANTS AWARDED TO FOREIGN ENTITIES ARE MONITORED BY REPORTING METHODS: NARRATIVE AND FINANCIAL REPORTS, PLUS OTHER DELIVERABLES TO PROVE THE USE OF FUNDS. |
| `/Return/ReturnData/IRS990ScheduleR/IdRelatedTaxExemptOrgGrp/DisregardedEntityName/BusinessNameLine1Txt` | 1 | 24 | WEROBOTICS (SWITZERLAND) |
| `/Return/ReturnData/IRS990ScheduleR/SupplementalInformationDetail/FormAndLineReferenceDesc` | 1 | 63 | PART II, COLUMN (B), WEROBOTICS (SWITZERLAND) PRIMARY ACTIVITY: |
| `/Return/ReturnData/IRS990ScheduleR/SupplementalInformationDetail/ExplanationTxt` | 1 | 551 | OUR MISSION IS TO SHIFT POWER FROM THE GLOBAL BACK TO THE LOCAL BY ENSURING THAT LOCAL EXPERTS WITH LOCAL KNOWLEDGE AND LIVED EXPERIENCE HAVE THE LEADERSHIP OPP |
| `/Return/ReturnData/IRS990/ProgSrvcAccomActyOtherGrp/Desc` | 1 | 69 | FUNDRAISING FOR THE REMODEL OF A BUILDING TO HOUSE COMMUNITY THEATER. |
| `/Return/ReturnData/IRS990/BooksInCareOfDetail/PersonNm` | 1 | 15 | CLASTON SUNANON |
| `/Return/ReturnData/IRS990/DoingBusinessAsName/BusinessNameLine1Txt` | 1 | 34 | DING DARLING WILDLIFE SOCIETY LAND |
| `/Return/ReturnData/IRS990/GrantsToDomesticOrgsGrp/ProgramServicesAmt` | 1 | 5 | 77000 |
| `/Return/ReturnData/IRS990/GrantsToDomesticIndividualsGrp/ProgramServicesAmt` | 1 | 5 | 32961 |
| `/Return/ReturnData/IRS990/PensionPlanContributionsGrp/ProgramServicesAmt` | 1 | 5 | 22279 |
| `/Return/ReturnData/IRS990ScheduleA/Form990ScheduleAPartVIGrp/ExplanationTxt` | 1 | 34 | GROSS SALES OF INVENTORY 2,889,995 |
| `/Return/ReturnData/IRS990ScheduleG/FundraisingEventInformationGrp/Event2Nm` | 1 | 15 | TARPON TOURNAME |
| `/Return/ReturnData/IRS990ScheduleI/SupplementalInformationDetail/FormAndLineReferenceDesc` | 1 | 34 | SCHEDULE I, PAGE 1, PART I, LINE 2 |
| `/Return/ReturnData/IRS990ScheduleI/SupplementalInformationDetail/ExplanationTxt` | 1 | 174 | THE SCHOLARSHIP COMMITTEE ISSUES A CHECK DIRECTLY TO THE AWARD RECIPIENT, WITH NO RESTRICTIONS PLACED ON THE USE OF THE SCHOLARSHIP FUNDS. THERE ARE NO MONITORI |
| `/Return/ReturnData/IRS990ScheduleJ/RltdOrgOfficerTrstKeyEmplGrp/PersonNm` | 1 | 19 | ANN MARIE E WILDMAN |
| `/Return/ReturnData/IRS990ScheduleJ/RltdOrgOfficerTrstKeyEmplGrp/TitleTxt` | 1 | 18 | EXECUTIVE DIRECTOR |
| `/Return/ReturnData/IRS990ScheduleM/OtherNonCashContriTableGrp/Desc` | 1 | 15 | SCULPTURE,BIKES |
| `/Return/ReturnData/IRS990/CompDisqualPersonsGrp/ProgramServicesAmt` | 1 | 5 | 96251 |
| `/Return/ReturnHeader/Filer/USAddress/CityNm` | 1 | 16 | Saint Petersburg |
| `/Return/ReturnData/IRS990/USAddress/CityNm` | 1 | 16 | Saint Petersburg |
| `/Return/ReturnData/IRS990/BooksInCareOfDetail/USAddress/CityNm` | 1 | 16 | Saint Petersburg |
| `/Return/ReturnData/IRS990/ContractorCompensationGrp/ContractorName/BusinessName/BusinessNameLine1Txt` | 1 | 46 | Omni Public Enterprises LLC DBA JW Consultants |
| `/Return/ReturnData/IRS990/InterestGrp/ProgramServicesAmt` | 1 | 1 | 0 |
| `/Return/ReturnData/IRS990ScheduleJ/SupplementalInformationDetail/ExplanationTxt` | 1 | 118 | Omni Public Enterprises LLC DBA JW Consultants paid Jennifer Webb $72,376 for services provided to Live Tampa Bay Inc. |
| `/Return/ReturnData/IRS990ScheduleL/BusTrInvolveInterestedPrsnGrp/NameOfInterested/BusinessName/BusinessNameLine1Txt` | 1 | 27 | Omni Public Enterprises LLC |

## 990EZ (8 sampled filings)

| Path | Seen in N filings | Max text len | Example snippet |
|---|---|---|---|
| `/Return/ReturnData/IRS990ScheduleO/SupplementalInformationDetail/FormAndLineReferenceDesc` | 23 | 53 | FORM 990-EZ, PART I, LINE 4 - OTHER INVESTMENT INCOME |
| `/Return/ReturnData/IRS990ScheduleO/SupplementalInformationDetail/ExplanationTxt` | 23 | 1439 | NAME: ST THERESE CATHOLIC SCHOOL ADDRESS: 1200 S. KENTON ST AURORA, CO 80010 CASH CONTRIBUTION: 5,000 NONCASH CONTRIBUTION: 1,444 NAME: ST JAMES CATHOLIC SCHOOL |
| `/Return/ReturnData/IRS990EZ/OfficerDirectorTrusteeEmplGrp/PersonNm` | 13 | 19 | Michele Laurinaitis |
| `/Return/ReturnData/IRS990EZ/ProgramSrvcAccomplishmentGrp/DescriptionProgramSrvcAccomTxt` | 12 | 260 | TO RAISE FUNDS ANNUALLY TO SUPPORT SPORTS PROGRAMS WITHIN CATHOLIC SCHOOLS THAT NEED FINANCIAL ASSISTANCE. SUPPORTED APPROXIMATELY 3,744 CHILDREN FROM THE CASH  |
| `/Return/ReturnData/IRS990EZ/ProgramSrvcAccomplishmentGrp/ProgramServiceExpensesAmt` | 9 | 6 | 139624 |
| `/Return/ReturnHeader/ReturnTs` | 8 | 25 | 2026-06-05T16:43:39-06:00 |
| `/Return/ReturnHeader/Filer/BusinessName/BusinessNameLine1Txt` | 8 | 44 | CENTER FOR BELGIAN CULTURE OF WESTERN IL INC |
| `/Return/ReturnHeader/BuildTS` | 8 | 20 | 2025-03-06 01:10:19Z |
| `/Return/ReturnData/IRS990EZ/PrimaryExemptPurposeTxt` | 8 | 217 | THE ASBESTOS AND LEAD ABATEMENT CONTRACTORS ASSOCIATION OF MICHIGAN IS CRAFTED FOR THE PURPOSE OF THE REPRESENTATION, BARGAINING AND ORGANIZING OF THE CONTRACTO |
| `/Return/ReturnData/IRS990EZ/TotalProgramServiceExpensesAmt` | 7 | 6 | 139624 |
| `/Return/ReturnData/IRS990EZ/BooksInCareOfDetail/USAddress/AddressLine1Txt` | 7 | 25 | 2451 ATRIUM WAY SUITE 300 |
| `/Return/ReturnData/IRS990EZ/OfficerDirectorTrusteeEmplGrp/TitleTxt` | 6 | 26 | DIRECTOR/AMINISTRATIVE APP |
| `/Return/ReturnHeader/PreparerFirmGrp/PreparerUSAddress/AddressLine1Txt` | 5 | 27 | 661 SUNNYBROOK RD SUITE 100 |
| `/Return/ReturnHeader/Filer/USAddress/AddressLine1Txt` | 5 | 23 | 9816 E CRESTLINE CIRCLE |
| `/Return/ReturnHeader/PreparerPersonGrp/PreparerPersonNm` | 5 | 28 | CHRISTOPHER SCOTT CPAPFS MST |
| `/Return/ReturnHeader/BusinessOfficerGrp/PersonNm` | 4 | 16 | Dave Laurinaitis |
| `/Return/ReturnHeader/PreparerFirmGrp/PreparerFirmName/BusinessNameLine1Txt` | 4 | 29 | VAN TIEGHEM & VAN TIEGHEM LTD |
| `/Return/ReturnData/IRS990EZ/ProgramServiceRevenueAmt` | 4 | 6 | 128281 |
| `/Return/ReturnData/IRS990EZ/WebsiteAddressTxt` | 4 | 32 | HTTPS://SAINTSEBASTIANDENVER.ORG |
| `/Return/ReturnData/IRS990EZ/BooksInCareOfDetail/PersonNm` | 3 | 17 | SYREETA N TALBERT |
| `/Return/ReturnHeader/Filer/InCareOfNm` | 2 | 18 | % NICHOLAS CORBETT |
| `/Return/ReturnData/IRS990EZ/BooksInCareOfDetail/BusinessName/BusinessNameLine1Txt` | 2 | 23 | VANTIEGHEM & VANTIEGHEM |
| `/Return/ReturnHeader/Filer/USAddress/CityNm` | 1 | 17 | GREENWOOD VILLAGE |
| `/Return/ReturnData/IRS990EZ/BooksInCareOfDetail/USAddress/CityNm` | 1 | 17 | GREENWOOD VILLAGE |
| `/Return/ReturnHeader/PreparerFirmGrp/PreparerUSAddress/CityNm` | 1 | 16 | CLINTON TOWNSHIP |
| `/Return/ReturnHeader/Filer/BusinessName/BusinessNameLine2Txt` | 1 | 35 | CONTRACTORS ASSOCIATION OF MICHIGAN |
| `/Return/ReturnData/IRS990ScheduleG/FundraisingEventInformationGrp/Event1Nm` | 1 | 26 | FARMER JIM NEAL GOLF EVENT |
| `/Return/ReturnData/IRS990ScheduleG/FundraisingEventInformationGrp/Event2Nm` | 1 | 28 | BENGEYFIELD/DYNAMIC COOKWARE |
| `/Return/ReturnData/TransferPrsnlBnftContractsDecl/DeclarationDesc` | 1 | 250 | THE ORGANIZATION DID NOT, DURING THE YEAR, RECEIVE ANY FUNDS, DIRECTLY,OR INDIRECTLY, TO PAY PREMIUMS ON A PERSONAL BENEFIT CONTRACT.THE ORGANIZATION, DID NOT,  |
| `/Return/ReturnData/ReasonableCauseExplanation/ExplanationTxt` | 1 | 14 | Medical Issues |

## 990PF (8 sampled filings)

| Path | Seen in N filings | Max text len | Example snippet |
|---|---|---|---|
| `/Return/ReturnData/IRS990PF/SupplementaryInformationGrp/GrantOrContributionPdDurYrGrp/GrantOrContributionPurposeTxt` | 25 | 12 | SEE ATTACHED |
| `/Return/ReturnData/IRS990PF/OfficerDirTrstKeyEmplInfoGrp/OfficerDirTrstKeyEmplGrp/USAddress/AddressLine1Txt` | 23 | 23 | 10375 Lake Vista Circle |
| `/Return/ReturnData/IRS990PF/SupplementaryInformationGrp/GrantOrContributionPdDurYrGrp/RecipientUSAddress/AddressLine1Txt` | 23 | 22 | 667 NEW HEMPSTEAD ROAD |
| `/Return/ReturnData/IRS990PF/SupplementaryInformationGrp/GrantOrContributionPdDurYrGrp/RecipientPersonNm` | 16 | 34 | GUARDIANS OF FLORIDA ANIMAL RESCUE |
| `/Return/ReturnData/IRS990PF/OfficerDirTrstKeyEmplInfoGrp/OfficerDirTrstKeyEmplGrp/PersonNm` | 13 | 22 | Sharon Fried-Buchalter |
| `/Return/ReturnHeader/ReturnTs` | 8 | 25 | 2026-06-22T17:48:09-04:00 |
| `/Return/ReturnHeader/Filer/BusinessName/BusinessNameLine1Txt` | 8 | 38 | JOHN PENN WHITESCARVERSRFOUNDATION INC |
| `/Return/ReturnHeader/BuildTS` | 8 | 20 | 2025-03-06 01:10:19Z |
| `/Return/ReturnData/IRS990PF/SupplementaryInformationGrp/GrantOrContributionPdDurYrGrp/RecipientBusinessName/BusinessNameLine1Txt` | 8 | 27 | CONGREGATION ANSHEI TRIBECA |
| `/Return/ReturnData/IRS990PF/StatementsRegardingActy4720Grp/NoncharitablePurposeInd` | 7 | 5 | false |
| `/Return/ReturnData/InvestmentsCorpStockSchedule/InvestmentsCorporateStockGrp/StockNm` | 7 | 28 | STRAT ADVISORS INTL FNDFILFX |
| `/Return/ReturnHeader/PreparerFirmGrp/PreparerFirmName/BusinessNameLine1Txt` | 6 | 34 | LEAVY HUCIK SHIFFLETT & SNYDER LLC |
| `/Return/ReturnHeader/Filer/USAddress/AddressLine1Txt` | 6 | 19 | 3030 NE 19TH STREET |
| `/Return/ReturnData/IRS990PF/SupplementaryInformationGrp/GrantOrContributionPdDurYrGrp/RecipientUSAddress/CityNm` | 6 | 16 | NORTH PALM BEACH |
| `/Return/ReturnData/GeneralExplanationAttachment/GeneralExplanationGrp/FormAndLineReferenceDesc` | 6 | 43 | Form 990PF-General Explanation Attachment 1 |
| `/Return/ReturnData/GeneralExplanationAttachment/GeneralExplanationGrp/MediumExplanationTxt` | 6 | 528 | PART XV SUPPLEMENTARY INFORMATION 3A NAME OF RECIPIENT - EQUINE ASSISTED THERAPIES OF SOUTH FLORIDA TO SUPPORT THE ORGANIZATIONS MISSION OF PROVIDING THERAPEUTI |
| `/Return/ReturnData/IRS990PF/StatementsRegardingActyGrp/LocationOfBooksUSAddress/AddressLine1Txt` | 5 | 19 | 3030 NE 19TH STREET |
| `/Return/ReturnHeader/BusinessOfficerGrp/PersonNm` | 5 | 27 | Jennifer Swanson Abbatacola |
| `/Return/ReturnData/IRS990PF/SummaryOfDirectChrtblActyGrp/Description1Txt` | 5 | 349 | Establish a trust for the sake of working with local, national, and international nonprofits and NGOs to allocate resources against specific conservation goals. |
| `/Return/ReturnData/OtherExpensesSchedule/OtherExpensesScheduleGrp/Desc` | 5 | 19 | church venue rental |
| `/Return/ReturnData/InvestmentsCorpBondsSchedule/InvestmentsCorporateBondsGrp/BondNm` | 5 | 30 | STRAT ADVISORS INC OPPO(FPIOX) |
| `/Return/ReturnData/IRS990ScheduleB/ContributorInformationGrp/ContributorUSAddress/AddressLine1Txt` | 4 | 20 | 1040 Avonoak Terrace |
| `/Return/ReturnHeader/PreparerFirmGrp/PreparerUSAddress/AddressLine1Txt` | 4 | 30 | 2810 E OAKLAND PK BLVD STE 300 |
| `/Return/ReturnData/IRS990PF/OfficerDirTrstKeyEmplInfoGrp/OfficerDirTrstKeyEmplGrp/USAddress/CityNm` | 4 | 15 | FORT LAUDERDALE |
| `/Return/ReturnData/IRS990PF/StatementsRegardingActyGrp/WebsiteAddressTxt` | 3 | 37 | https//www.rescuemissionunlimited.com |
| `/Return/ReturnData/AccountingFeesSchedule/AccountingFeesDetail/CategoryTxt` | 3 | 15 | ACCOUNTING FEES |
| `/Return/ReturnHeader/PreparerPersonGrp/PreparerPersonNm` | 3 | 18 | CARLYSLE SIMMS CPA |
| `/Return/ReturnData/IRS990PF/CapGainsLossTxInvstIncmDetail/CapGainsLossTxInvstIncmGrp/PropertyDesc` | 3 | 27 | CAPITAL GAINS DISTRIBUTIONS |
| `/Return/ReturnData/IRS990PF/SumOfProgramRelatedInvstGrp/Description1Txt` | 2 | 3 | N/A |
| `/Return/ReturnData/IRS990ScheduleB/ContributorInformationGrp/ContributorPersonNm` | 2 | 22 | miriam riffel-dalinger |
| `/Return/ReturnData/OtherProfessionalFeesSchedule/OtherProfessionalFeesDetail/CategoryTxt` | 2 | 15 | management fees |
| `/Return/ReturnData/SubstantialContributorsSch/SubstantialContributorDetail/PersonNm` | 2 | 22 | Miriam Riffel-Dalinger |
| `/Return/ReturnData/SubstantialContributorsSch/SubstantialContributorDetail/USAddress/AddressLine1Txt` | 2 | 25 | 1545 N Verdugo Rd Ste 115 |
| `/Return/ReturnData/IRS990PF/StatementsRegardingActyGrp/PersonsWithBooksName/BusinessNameLine1Txt` | 2 | 20 | Pimwadee Limsirichai |
| `/Return/ReturnData/IRS990PF/OfficerDirTrstKeyEmplInfoGrp/OfficerDirTrstKeyEmplGrp/TitleTxt` | 2 | 19 | President Treasurer |
| `/Return/ReturnData/IRS990PF/SupplementaryInformationGrp/ApplicationSubmissionInfoGrp/RecipientUSAddress/AddressLine1Txt` | 2 | 19 | 3030 NE 19TH STREET |
| `/Return/ReturnData/IRS990PF/SupplementaryInformationGrp/ApplicationSubmissionInfoGrp/FormAndInfoAndMaterialsTxt` | 2 | 234 | THE FOUNDATION PROVIDES GRANTS TO NONPROFIT ORGANIZATIONS THAT PROVIDE EDUCATION AND SUPPORT FOR ANIMAL AND WILDLIFE CARE, RESCUE, PROTESTION AND CONSERVATION.  |
| `/Return/ReturnData/IRS990PF/SupplementaryInformationGrp/ApplicationSubmissionInfoGrp/SubmissionDeadlinesTxt` | 2 | 4 | NONE |
| `/Return/ReturnData/InvestmentsOtherSchedule2/InvestmentsOtherGrp/CategoryOrItemTxt` | 2 | 34 | FIDELITY GOV CASH RESERVES (FDRXX) |
| `/Return/ReturnData/DepreciationSchedule/DepreciationPropertyGrp/PropertyDesc` | 2 | 31 | 5655 South Sossaman Rd Building |
| `/Return/ReturnData/OtherNotesLoansRcvblShortSch2/OtherNotesLoansRcvblShortGrp/Organization501c3Name/BusinessNameLine1Txt` | 1 | 15 | LOAN RECEIVABLE |
| `/Return/ReturnData/TaxesSchedule/TaxesDetail/CategoryTxt` | 1 | 19 | US TREASURY PENALTY |
| `/Return/ReturnHeader/Filer/BusinessName/BusinessNameLine2Txt` | 1 | 18 | and Orchestra Corp |
| `/Return/ReturnData/IRS990PF/StatementsRegardingActyGrp/IndividualWithBooksNm` | 1 | 19 | Jennifer Abbatacola |
| `/Return/ReturnData/ReasonableCauseExplanation/ExplanationTxt` | 1 | 237 | I filed online for the first time to save some money. My father died. I was his caregiver. I filed the wrong form. It was rejected. I was catching up on paperwo |
| `/Return/ReturnHeader/BusinessOfficerGrp/PersonTitleTxt` | 1 | 18 | Executive Director |
| `/Return/ReturnHeader/Filer/USAddress/CityNm` | 1 | 15 | FORT LAUDERDALE |
| `/Return/ReturnData/IRS990PF/StatementsRegardingActyGrp/LocationOfBooksUSAddress/CityNm` | 1 | 15 | FORT LAUDERDALE |
| `/Return/ReturnData/IRS990PF/SupplementaryInformationGrp/ApplicationSubmissionInfoGrp/RecipientPersonNm` | 1 | 34 | FOLKE PETERSON WILDLIFE CENTER INC |
| `/Return/ReturnData/IRS990PF/SupplementaryInformationGrp/ApplicationSubmissionInfoGrp/RecipientUSAddress/CityNm` | 1 | 15 | FORT LAUDERDALE |
| `/Return/ReturnData/IRS990PF/SummaryOfDirectChrtblActyGrp/Description2Txt` | 1 | 251 | Air transportation for individuals who need to travel long distances for critical medical treatment. This service will provide cover flights for patients, famil |
| `/Return/ReturnData/IRS990PF/SummaryOfDirectChrtblActyGrp/Description3Txt` | 1 | 280 | Introduce young people to the world of aviation by hosting educational programs for local schools. The foundation will extend invitations for students to visit  |
| `/Return/ReturnData/IRS990PF/SummaryOfDirectChrtblActyGrp/Description4Txt` | 1 | 264 | Support the development and ongoing maintenance of the Serene Rose Garden at Mesa Community College, creating a peaceful space for students, faculty, and the br |
| `/Return/ReturnData/OtherIncomeSchedule2/OtherIncomeDetail/Desc` | 1 | 38 | Rental Income - Noninvestment Property |
