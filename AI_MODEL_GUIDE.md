# AI Model Development Guide - PV Autofill Project

## Overview

This guide outlines the development of an AI model using Prophet for time series forecasting based on vehicle inspection data from the PV Autofill project. The model will predict various business metrics using the extracted Excel data.

## Project Structure

```
pv-autofill/
├── pv_autofill.py          # Main data extraction script
├── config.py               # Configuration settings
├── clean_duplicates.py     # Data cleaning utility
├── requirements.txt        # Python dependencies
├── dataset/               # Data storage directory
├── ai_model/              # AI model development directory
│   ├── data_preparation.py
│   ├── prophet_models.py
│   ├── model_evaluation.py
│   ├── forecasting.py
│   └── visualization.py
└── AI_MODEL_GUIDE.md      # This guide
```

## Data Structure Analysis

### Current Excel Headers

Based on the existing `EXCEL_HEADERS` in `config.py` (with irrelevant fields ignored):

```python
EXCEL_HEADERS = [
    "DATE",           # Inspection date (DD/MM/YYYY)
    "N° PV",          # Report number
    "DESCRIPTIONS",   # Client information
    "COUPON",         # Discount amount
    "C/CV",           # Control/Re-inspection (C/CV)
    "IMMATRI",        # Vehicle registration
    "CONTACT",        # Phone number
    "CAT",            # Vehicle category (A, B, C, D, etc.)
    "DATE P.V",       # Next visit date
    "pht",            # Amount excluding tax
    "TVA",            # Tax amount
    "PTTC",           # Total amount including tax
]
```

> **Note:** The fields `ACCEPTE`, `REFUS`, and `N° SCELLES` are ignored in all analyses and models, as their values are not relevant or predictable from available data.

### Selected Headers for AI Model

We will use these headers for the AI model:

- **DATE** - Primary time series variable
- **N° PV** - Unique identifier
- **DESCRIPTIONS** - Client information
- **COUPON** - Discount amounts
- **C/CV** - Control type
- **IMMATRI** - Vehicle registration
- **CONTACT** - Contact information
- **CAT** - Vehicle category
- **DATE P.V** - Next visit date
- **pht** - Amount excluding tax
- **TVA** - Tax amount
- **PTTC** - Total amount including tax

## AI Model Development Plan

### Phase 1: Data Preparation

#### 1.1 Data Collection Script

Create `ai_model/data_preparation.py` to:

- Read Excel files from the existing structure
- Aggregate data by date
- Handle missing values and outliers
- Create time series datasets

#### 1.2 Data Aggregation Strategies

- **Daily aggregations**: Count of inspections, total revenue, average amounts
- **Weekly aggregations**: Weekly patterns and trends
- **Monthly aggregations**: Seasonal patterns
- **Category-based aggregations**: By vehicle type (CAT)
- **Revenue aggregations**: By pht, TVA, PTTC

### Phase 2: Prophet Model Implementation

#### 2.1 Core Forecasting Models

Create `ai_model/prophet_models.py` with models for:

1. **Daily Vehicle Volume Prediction**

   - Input: Daily count of inspections
   - Output: Forecasted daily volume
   - Features: Day of week, month, holidays

2. **Revenue Forecasting**

   - Input: Daily PTTC totals
   - Output: Forecasted daily revenue
   - Features: Seasonal patterns, coupon effects

3. **Category Distribution Prediction**
   - Input: Daily counts by vehicle category
   - Output: Forecasted category distribution
   - Features: Vehicle type trends

#### 2.2 Advanced Models

4. **Customer Return Prediction**

   - Input: Vehicle registration frequency
   - Output: Likelihood of return visits
   - Features: Customer segmentation

5. **Coupon Impact Analysis**
   - Input: Coupon usage patterns
   - Output: Revenue impact of coupons
   - Features: Discount effectiveness

### Phase 3: Model Evaluation

#### 3.1 Evaluation Metrics

Create `ai_model/model_evaluation.py` to assess:

- **MAPE** (Mean Absolute Percentage Error)
- **RMSE** (Root Mean Square Error)
- **MAE** (Mean Absolute Error)
- **Forecast accuracy** by time horizon

#### 3.2 Cross-Validation

- Time series cross-validation
- Out-of-sample testing
- Model comparison

### Phase 4: Production Implementation

#### 4.1 Forecasting Pipeline

Create `ai_model/forecasting.py` for:

- Automated daily predictions
- Real-time model updates
- Alert systems for anomalies

#### 4.2 Visualization Dashboard

Create `ai_model/visualization.py` for:

- Interactive charts
- Forecast vs actual comparisons
- Business insights dashboard

## Implementation Steps

### Step 1: Environment Setup

```bash
# Install additional dependencies for AI model
pip install prophet pandas numpy matplotlib seaborn plotly scikit-learn
```

### Step 2: Data Extraction Module

```python
# ai_model/data_extractor.py
import pandas as pd
from pathlib import Path
from openpyxl import load_workbook
from datetime import datetime
import logging

class DataExtractor:
    def __init__(self, excel_folder_path):
        self.excel_folder = Path(excel_folder_path)
        self.logger = logging.getLogger(__name__)

    def load_all_excel_data(self):
        """Load all Excel files and combine into single DataFrame"""
        all_data = []

        for excel_file in self.excel_folder.rglob("*.xlsx"):
            try:
                wb = load_workbook(excel_file)
                ws = wb.active

                # Convert worksheet to DataFrame
                data = []
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if any(cell is not None for cell in row):
                        data.append(row)

                if data:
                    df = pd.DataFrame(data, columns=EXCEL_HEADERS)
                    df['source_file'] = excel_file.name
                    all_data.append(df)

                wb.close()

            except Exception as e:
                self.logger.error(f"Error loading {excel_file}: {e}")

        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return self.clean_data(combined_df)
        else:
            return pd.DataFrame()

    def clean_data(self, df):
        """Clean and prepare data for modeling"""
        # Convert DATE to datetime
        df['DATE'] = pd.to_datetime(df['DATE'], format='%d/%m/%Y', errors='coerce')

        # Convert numeric columns
        numeric_cols = ['COUPON', 'pht', 'TVA', 'PTTC']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Remove rows with invalid dates
        df = df.dropna(subset=['DATE'])

        # Sort by date
        df = df.sort_values('DATE')

        return df
```

### Step 3: Prophet Model Implementation

```python
# ai_model/prophet_models.py
import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import datetime, timedelta
import logging

class PVProphetModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}

    def prepare_daily_data(self, df):
        """Aggregate data by date for daily forecasting"""
        daily_data = df.groupby('DATE').agg({
            'N° PV': 'count',  # Daily inspection count
            'PTTC': 'sum',      # Daily revenue
            'pht': 'sum',       # Daily revenue excluding tax
            'TVA': 'sum',       # Daily tax revenue
            'COUPON': 'sum',    # Daily coupon usage
            # No rejection/acceptance fields
        }).reset_index()

        return daily_data

    def create_volume_model(self, daily_data):
        """Create Prophet model for daily inspection volume"""
        # Prepare data for Prophet
        prophet_data = daily_data[['DATE', 'N° PV']].copy()
        prophet_data.columns = ['ds', 'y']

        # Create and fit model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )

        # Add custom seasonality for business days
        model.add_seasonality(
            name='weekly',
            period=7,
            fourier_order=3
        )

        model.fit(prophet_data)
        return model

    def create_revenue_model(self, daily_data):
        """Create Prophet model for daily revenue"""
        prophet_data = daily_data[['DATE', 'PTTC']].copy()
        prophet_data.columns = ['ds', 'y']

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )

        model.fit(prophet_data)
        return model

    def train_all_models(self, df):
        """Train all Prophet models"""
        daily_data = self.prepare_daily_data(df)

        # Train volume model
        self.models['volume'] = self.create_volume_model(daily_data)

        # Train revenue model
        self.models['revenue'] = self.create_revenue_model(daily_data)

        self.logger.info("All models trained successfully")
        return daily_data

    def forecast(self, periods=30):
        """Generate forecasts for all models"""
        forecasts = {}

        for model_name, model in self.models.items():
            future = model.make_future_dataframe(periods=periods)
            forecast = model.predict(future)
            forecasts[model_name] = forecast

        return forecasts
```

### Step 4: Model Evaluation

```python
# ai_model/model_evaluation.py
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
import logging

class ModelEvaluator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_metrics(self, actual, predicted):
        """Calculate evaluation metrics"""
        mae = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        return {
            'MAE': mae,
            'RMSE': rmse,
            'MAPE': mape
        }

    def evaluate_models(self, daily_data, forecasts):
        """Evaluate all models"""
        results = {}

        for model_name, forecast in forecasts.items():
            if model_name == 'volume':
                actual = daily_data['N° PV'].values
                predicted = forecast['yhat'].values[:len(actual)]
            elif model_name == 'revenue':
                actual = daily_data['PTTC'].values
                predicted = forecast['yhat'].values[:len(actual)]

            metrics = self.calculate_metrics(actual, predicted)
            results[model_name] = metrics

            self.logger.info(f"{model_name} model metrics: {metrics}")

        return results
```

### Step 5: Visualization

```python
# ai_model/visualization.py
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

class ModelVisualizer:
    def __init__(self):
        plt.style.use('seaborn-v0_8')

    def plot_forecasts(self, daily_data, forecasts):
        """Create comprehensive forecast plots"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Daily Inspection Volume', 'Daily Revenue'),
            vertical_spacing=0.1
        )

        # Volume forecast
        fig.add_trace(
            go.Scatter(
                x=daily_data['DATE'],
                y=daily_data['N° PV'],
                name='Actual Volume',
                mode='markers+lines'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=forecasts['volume']['ds'],
                y=forecasts['volume']['yhat'],
                name='Predicted Volume',
                mode='lines',
                line=dict(dash='dash')
            ),
            row=1, col=1
        )

        # Revenue forecast
        fig.add_trace(
            go.Scatter(
                x=daily_data['DATE'],
                y=daily_data['PTTC'],
                name='Actual Revenue',
                mode='markers+lines'
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=forecasts['revenue']['ds'],
                y=forecasts['revenue']['yhat'],
                name='Predicted Revenue',
                mode='lines',
                line=dict(dash='dash')
            ),
            row=2, col=1
        )

        fig.update_layout(
            height=700,
            title_text="PV Autofill Forecasting Models",
            showlegend=True
        )

        return fig
```

## Usage Examples

### Basic Usage

```python
# Example usage script
from ai_model.data_extractor import DataExtractor
from ai_model.prophet_models import PVProphetModel
from ai_model.model_evaluation import ModelEvaluator
from ai_model.visualization import ModelVisualizer

# Initialize components
extractor = DataExtractor("path/to/excel/folder")
model = PVProphetModel()
evaluator = ModelEvaluator()
visualizer = ModelVisualizer()

# Load and prepare data
df = extractor.load_all_excel_data()
daily_data = model.prepare_daily_data(df)

# Train models
model.train_all_models(df)

# Generate forecasts
forecasts = model.forecast(periods=30)

# Evaluate models
evaluation_results = evaluator.evaluate_models(daily_data, forecasts)

# Create visualizations
forecast_plot = visualizer.plot_forecasts(daily_data, forecasts)

# Save results
forecast_plot.write_html("forecasts.html")
```

## Business Applications

### 1. Resource Planning

- Predict daily inspection volume for staff scheduling
- Forecast revenue for budget planning
- Identify peak periods for capacity planning

### 2. Customer Insights

- Analyze customer return patterns
- Segment customers by behavior
- Predict customer lifetime value

### 3. Financial Planning

- Revenue forecasting for business planning
- Coupon impact analysis
- Tax revenue predictions

## Next Steps

1. **Implement the data extraction module**
2. **Create the Prophet models**
3. **Add model evaluation**
4. **Build visualization dashboard**
5. **Deploy production forecasting system**
6. **Add real-time monitoring and alerts**

## Dependencies

Add to `requirements.txt`:

```
prophet>=1.1.4
pandas>=1.5.0
numpy>=1.21.0
matplotlib>=3.5.0
seaborn>=0.11.0
plotly>=5.0.0
scikit-learn>=1.0.0
```

This guide provides a comprehensive framework for building AI models using Prophet based on your existing PV autofill project data structure.
