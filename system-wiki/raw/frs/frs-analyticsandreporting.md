Module 5: Analytics and Reporting
a. Statistical Query Engine
i.        National Analyst can query aggregated incident data from Central Database (PostgreSQL Materialized Views)
ii.      System shall support filtering by: (FastAPI Depends (Query Params))
·         Date range (from–to)
·         Incident type
·         Location (municipality, province, region)
·         Casualty severity
·         Property damage range
iii.    System shall provide the following analytics views: (SQLAlchemy + Pandas)
·         Total incidents by month, quarter, year
·         Incident distribution by type (pie chart) (Recharts)
·         Geographic heatmap of incident frequency (React Leaflet + Leaflet.heat)
·         Trend analysis (line graph of incidents over time) (Recharts (ComposedChart))
·         Top 10 municipalities with highest incident count
·         Average response time by region
b. Query Execution
i.        National Analyst submits query via “Query Parameters / Analysis Request” form 
ii.      System sends query to Analytics via Query process
iii.    Analytics via Query fetches data from Central Database using “Aggregate Data” request
iv.    Central Database responds with query results
v.      System generates “Statistical Trends and Reports” output
c. Report Export
i.        National Analyst can export reports in the following formats: 
o   PDF (formatted for printing) (WeasyPrint)
o   Excel (.xlsx) with raw data (Pandas (to_excel, to_csv))
o   CSV (comma-separated values)
ii.      Exported reports shall include:
·         Report title and description
·         Query parameters (filters applied)
·         Data visualization (charts/graphs)
·         Summary statistics
·         Generation timestamp and analyst user ID
iii.    System shall log all report exports in audit trail (FastAPI Background Tasks)
