# Expense Tracker Application

This project was created as a practical personal tool to help a friend who owned a sales trailer better understand her cash flow and monthly expenses. Despite having a healthy sales volume, she still faced recurring costs that were difficult to monitor without a clear structure. The goal was simply to organize the available financial information and make it easier to identify spending patterns and opportunities for reduction.

This is not a finished commercial product or a fully production-ready solution. It was built as a support tool for analysis and day-to-day decision-making, especially for a small business context where a clearer view of expenses can make a meaningful difference.

## Project Structure

```
expense-tracker-excel
├── data/
│   ├── pdf/
│   │   └── Silvana/
│   ├── expenses.xlsx
│   └── sample_data/
├── scripts/
│   ├── process_expenses.py
│   ├── process_pdf.py
│   ├── process_txt.py
│   ├── process_excel.py
│   └── generate_sample_expenses.py
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

## Real-World Impact

This tool was used in a real scenario with a sales trailer business to review a few months of financial data and organize the information in a simpler way. Even though the business had a healthy sales flow, the analysis helped identify areas where spending could be better controlled. In that context, the project proved useful in highlighting unnecessary costs and supporting more disciplined financial decisions.

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```
   cd expense-tracker-excel
   ```

3. Install the required Python libraries:
   ```
   pip install -r requirements.txt
   ```

4. Place your financial files in the appropriate folder under the `data/` directory and run the processing scripts.

## Usage

- Use the dashboard script in `scripts/process_expenses.py` to load and analyze the data.
- Review the generated summaries and reports to identify cost reduction opportunities.
- Adjust categories and analysis rules based on your specific financial context.

## Contributing

Contributions are welcome. If you have suggestions for improving data processing, reporting, or usability, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.