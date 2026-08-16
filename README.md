# Expense Tracker Application

This project was created as a practical personal tool to help a friend who owned a sales trailer better understand her cash flow and monthly expenses. Despite having a healthy sales volume, she still faced recurring costs that were difficult to monitor without a clear structure. The goal was simply to organize the available financial information and make it easier to identify spending patterns and opportunities for reduction.

This is not a finished commercial product or a fully production-ready solution. It was built as a support tool for analysis and day-to-day decision-making, especially for a small business context where a clearer view of expenses can make a meaningful difference.

## Project Structure

```
expense-tracker-excel
├── main.py
├── app/
│   └── app.py
├── services/
│   ├── data_loader.py
│   ├── normalization_service.py
│   ├── financial_service.py
│   ├── alert_service.py
│   └── forecast_service.py
├── domain/
│   ├── enums.py
│   ├── models.py
│   └── validators.py
├── ui/
│   ├── main_window.py
│   ├── dashboard_window.py
│   ├── styles.py
│   └── widgets.py
├── data/
│   ├── pdf/
│   │   └── Silvana/
│   ├── expenses.xlsx
│   └── sample_data/
├── scripts/
│   ├── process_pdf.py
│   ├── process_txt.py
│   ├── process_excel.py
│   └── generate_sample_expenses.py
├── legacy/
│   └── process_expenses.py
├── tests/
│   └── test_services.py
├── docs/
│   └── requirements.md
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

## Main Objective

This project was developed as a simple support tool for financial review, especially in small business and service-based contexts where the owner needs a clearer view of:

- income and expense trends;
- cash flow by month;
- category-based spending analysis;
- recurring costs and opportunities for reduction;
- historical reports for better planning and follow-up.

## Key Features

- Import and organize expense data from PDF, TXT, and Excel sources.
- Categorize expenses and group them by type and period.
- Generate monthly and daily financial summaries.
- Analyze income versus expenses to assess financial health.
- Highlight recurring costs and identify patterns of unnecessary spending.
- Present financial results in a clear and usable dashboard interface.

## Screenshots

### Goal and Alerts

![Metas e alertas](resource/screenshots/Metas%20e%20alertas.png)

In the "Metas e Alertas" view, we could clearly see that the business owner had not yet defined her spending limits in a structured way. This made it difficult to compare actual costs against realistic targets and showed that a stronger financial education process was needed. The data helped reveal the need for more disciplined planning and more informed decision-making.

### Monthly Spending

![Gastos Mensais](resource/screenshots/Gastos%20Mensais.png)

In the "Gastos Mensais" view, we were able to follow the improvement in the business cash flow over time. However, the expense level was still too high, and the data showed that stronger cost control was still necessary. These findings were useful in reorienting the business strategy and focusing attention on the categories that required more careful management.

### Central Dashboard

![Dashboard Central](resource/screenshots/DashBoard%20Central.png)

The "Dashboard Central" allowed the owner to monitor day-to-day performance and understand the overall financial summary in a practical and immediate way. It made it easier to identify trends, evaluate the current situation, and make faster operational decisions based on real data.

## Real-World Impact

This tool was used in a real scenario with a sales trailer business to review a few months of financial data and organize the information in a simpler way. Even though the business had a healthy sales flow, the analysis helped identify areas where spending could be better controlled. In that context, the project proved useful in highlighting unnecessary costs and supporting more disciplined financial decisions.

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/Marchesiii/expense-tracker-excel
   ```

2. Navigate to the project directory:
   ```
   cd expense-tracker-excel
   ```

3. Install the required Python libraries:
   ```
   pip install -r requirements.txt
   ```

4. Place your financial files in the appropriate folder under the `data/YourName` directory and run the processing scripts.

## Usage

- Run `python main.py` to launch the application.
- From the interface, load your data, review the dashboard, summaries, and reports.
- Adjust categories and analysis rules based on your specific financial context.

## Contributing

Contributions are welcome. If you have suggestions for improving data processing, reporting, or usability, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.