# Non-Conformance (NC) Data Analysis Dashboard

A comprehensive Streamlit dashboard for analyzing Non-Conformance data from Google Sheets, built for Calyx Containers quality management.

![Dashboard Preview](https://via.placeholder.com/800x400?text=NC+Dashboard+Preview)

## 🚀 Features

### 📋 Open NCs Status Tracker
- Real-time count of open NCs grouped by status
- Interactive metric cards and gauges
- Priority breakdown visualization
- Status distribution charts

### ⏱️ Aging Analysis Dashboard
- Aging buckets: 0-30, 31-60, 61-90, 90+ days
- Date range filtering
- Average, median, and max age metrics
- Critical aging alerts for 90+ day NCs

### 💰 Cost of Rework Analysis
- Time period filters: daily, weekly, monthly, quarterly, yearly
- Interactive date range selector
- Trend analysis with moving averages
- Cost distribution by customer and issue type

### ✅ Cost Avoided Analysis
- Same time period functionality as Cost of Rework
- Comparative analysis (Rework vs Avoided)
- ROI calculation and visualization
- Summary statistics

### 👥 Customer Analysis
- NC count by customer (descending bar chart)
- Interactive drill-down capability
- Customer concentration analysis (80/20)
- Comprehensive comparison table

### 📊 Issue Type Pareto Chart
- Pareto analysis with cumulative percentage line
- 80% threshold visualization
- External/Internal filter
- Date range filtering

## 📁 Project Structure

```
nc-dashboard/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .streamlit/
│   ├── config.toml           # Streamlit configuration
│   └── secrets.toml.template # Secrets template
├── src/
│   ├── __init__.py           # Package initialization
│   ├── data_loader.py        # Google Sheets data loading
│   ├── kpi_cards.py          # Open NC Status Tracker
│   ├── aging_analysis.py     # Aging Analysis module
│   ├── cost_analysis.py      # Cost of Rework & Cost Avoided
│   ├── customer_analysis.py  # Customer Analysis module
│   ├── pareto_chart.py       # Issue Type Pareto
│   └── utils.py              # Utility functions
├── tests/
│   ├── __init__.py
│   └── test_dashboard.py     # Unit tests
└── config/
    └── (optional configs)
```

## 🛠️ Installation

### Prerequisites
- Python 3.9 or higher
- Google Cloud account with Sheets API enabled
- Google Sheet with NC data

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-org/nc-dashboard.git
cd nc-dashboard
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Google Sheets API

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable the Google Sheets API and Google Drive API

2. **Create Service Account**
   - Go to APIs & Services → Credentials
   - Create a Service Account
   - Generate a JSON key file
   - Download the JSON key

3. **Share Your Google Sheet**
   - Open your Google Sheet with NC data
   - Click Share
   - Add the service account email (from JSON: `client_email`)
   - Give it Viewer access

### Step 5: Configure Secrets

1. Copy the secrets template:
```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

2. Edit `.streamlit/secrets.toml` with your credentials:
```toml
[google_sheets]
spreadsheet_id = "your-spreadsheet-id"
sheet_name = "Non-Conformance Details"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

### Step 6: Run the Dashboard
```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 📊 Data Requirements

Your Google Sheet must have a tab named "Non-Conformance Details" with these columns:

| Column | Description | Type |
|--------|-------------|------|
| Year | Year of NC | Number |
| Week | Week number | Number |
| External Or Internal | Source classification | Text |
| NC Number | Unique NC identifier | Text |
| Priority | High/Medium/Low | Text |
| Sales Order | Related sales order | Text |
| Related Ticket Numbers | Support tickets | Text |
| Customer | Customer name | Text |
| Issue Type | Type of defect/issue | Text |
| Employee Responsible | Assigned employee | Text |
| Defect Summary | Description of issue | Text |
| Status | Open/In Progress/Closed/etc. | Text |
| Affected Items | Items impacted | Text |
| On Time Ship Date | Target ship date | Date |
| Total Quantity Affected | Number of units | Number |
| Cost of Rework | Rework cost in USD | Number |
| Cost Avoided | Savings in USD | Number |
| Date Submitted | NC creation date | Date |
| Equipment | Related equipment | Text |
| First Article Completed | Yes/No | Text |
| First Article Inspector | Inspector name | Text |

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_dashboard.py -v
```

## 🚀 Deployment

### Streamlit Community Cloud (Recommended)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Add secrets in the Streamlit Cloud dashboard
5. Deploy!

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t nc-dashboard .
docker run -p 8501:8501 nc-dashboard
```

### Environment Variables (Alternative to secrets.toml)

For production deployments, you can use environment variables:

```bash
export GOOGLE_SHEETS_SPREADSHEET_ID="your-id"
export GCP_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
```

## 🔧 Configuration

### Streamlit Theme (.streamlit/config.toml)

```toml
[theme]
primaryColor = "#1E3A5F"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F8F9FA"
textColor = "#262730"
font = "sans serif"
```

### Data Caching

Data is cached for 5 minutes by default. To change:

```python
# In src/data_loader.py
@st.cache_data(ttl=600)  # Change TTL in seconds
def load_nc_data():
    ...
```

## 📈 Performance Tips

1. **Data Caching**: The dashboard uses Streamlit's caching to minimize API calls
2. **Batch Operations**: Large datasets are processed in batches
3. **Lazy Loading**: Charts are rendered on-demand per tab
4. **Efficient Queries**: Use the sidebar filters to reduce data size

## 🐛 Troubleshooting

### "Spreadsheet not found" Error
- Verify the spreadsheet ID in secrets.toml
- Ensure the service account has access to the sheet

### "Authentication failed" Error
- Check that all service account credentials are correct
- Verify the private key includes proper newlines (`\n`)

### "No data available" Warning
- Confirm the sheet name matches exactly
- Check that the sheet has data in the expected columns

### Slow Performance
- Reduce date ranges in filters
- Enable data export and analyze locally for large datasets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary to Calyx Containers. All rights reserved.

## 👥 Contact

**Xander** - Revenue Operations Manager
- Calyx Containers

---

Built with ❤️ using [Streamlit](https://streamlit.io) and [Plotly](https://plotly.com)
