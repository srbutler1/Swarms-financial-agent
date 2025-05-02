"""
PDF report generation utilities for Sam Butler Investment Agency.
"""
import os
import time
from pathlib import Path
from datetime import datetime
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import KeepTogether
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
import matplotlib.pyplot as plt
import matplotlib
import yfinance as yf
import pandas as pd
matplotlib.use('Agg')  # Use non-interactive backend

# Create directories for storing assets
CHART_DIR = Path("outputs/charts")
CHART_DIR.mkdir(exist_ok=True, parents=True)

REPORT_DIR = Path("outputs/reports")
REPORT_DIR.mkdir(exist_ok=True, parents=True)

# Define corporate colors for consistent branding
CORPORATE_COLORS = {
    'primary': colors.HexColor("#143b86"),  # Dark blue
    'secondary': colors.HexColor("#3a66b0"),  # Medium blue
    'accent': colors.HexColor("#e06d10"),  # Orange accent
    'background': colors.HexColor("#f5f7fa"),  # Light gray background
    'text': colors.HexColor("#333333"),  # Dark gray text
    'positive': colors.HexColor("#157f3d"),  # Green for positive returns
    'negative': colors.HexColor("#c42f30"),  # Red for negative returns
}

def create_stock_chart(ticker, period="3mo"):
    """Create a price chart for a stock."""
    try:
        # Get stock data
        data = yf.download(ticker, period=period)
        if data.empty:
            return None
            
        # Create a simple price chart
        plt.figure(figsize=(8, 4), facecolor='white')
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Plot price line
        plt.plot(data.index, data['Close'], linewidth=2, color='#3a66b0', label='Price')
        
        # Add moving averages
        if len(data) > 20:
            data['MA20'] = data['Close'].rolling(window=20).mean()
            plt.plot(data.index, data['MA20'], linewidth=1.5, linestyle="--", 
                     color="#e06d10", label="20-day MA")
        
        if len(data) > 50:
            data['MA50'] = data['Close'].rolling(window=50).mean()
            plt.plot(data.index, data['MA50'], linewidth=1.5, linestyle="--", 
                     color="#c42f30", label="50-day MA")
                     
        # Calculate and display return
        if len(data) > 1:
            start_price = data['Close'].iloc[0].item()  # Get scalar value
            end_price = data['Close'].iloc[-1].item()  # Get scalar value
            percent_change = ((end_price - start_price) / start_price) * 100
            color = '#157f3d' if percent_change >= 0 else '#c42f30'
            label = f"{percent_change:.1f}% {'▲' if percent_change >= 0 else '▼'}"
            plt.figtext(0.15, 0.04, label, color=color, fontsize=12, weight='bold')
        
        # Enhance styling
        plt.title(f"{ticker} - Price History ({period})", fontsize=14, fontweight='bold', color='#143b86')
        plt.ylabel("Price ($)", color='#333333')
        plt.grid(True, linestyle="--", alpha=0.7, color='#dddddd')
        plt.legend(loc='upper left', frameon=True)
        plt.tight_layout()
        
        # Save the simple chart
        chart_path = CHART_DIR / f"{ticker}_price_chart.png"
        plt.savefig(chart_path, dpi=150)
        plt.close()
        
        return chart_path  # Return the basic chart as a fallback
        
    except Exception as e:
        print(f"Error creating chart for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_performance_comparison_chart(tickers):
    """Create a comparative performance chart for multiple stocks."""
    try:
        # Get data for all tickers
        end_date = datetime.now()
        start_date = end_date - datetime.timedelta(days=90)
        data = yf.download(tickers, start=start_date, end=end_date)['Close']
        
        if data.empty:
            return None
            
        # Normalize data to starting price = 100
        normalized_data = data.copy()
        for ticker in tickers:
            if ticker in normalized_data.columns:
                first_valid = normalized_data[ticker].first_valid_index()
                if first_valid is not None:
                    base_value = normalized_data.loc[first_valid, ticker].item()  # Get scalar value
                    normalized_data[ticker] = normalized_data[ticker] / base_value * 100
        
        # Create the chart
        plt.figure(figsize=(10, 6), facecolor='white')
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Use a colormap for multiple lines
        colors = plt.cm.tab10(np.linspace(0, 1, len(tickers)))
        
        # Plot each ticker
        for i, ticker in enumerate(tickers):
            if ticker in normalized_data.columns:
                plt.plot(normalized_data.index, normalized_data[ticker], 
                         linewidth=2, label=ticker, color=colors[i])
        
        plt.title("Comparative Performance (Base = 100)", fontsize=14, 
                  fontweight='bold', color='#143b86')
        plt.ylabel("Normalized Price", color='#333333')
        plt.grid(True, linestyle="--", alpha=0.7, color='#dddddd')
        plt.legend(loc='upper left', frameon=True)
        plt.tight_layout()
        
        # Save the chart
        chart_path = CHART_DIR / f"comparative_performance.png"
        plt.savefig(chart_path, dpi=150)
        plt.close()
        
        return chart_path
    except Exception as e:
        print(f"Error creating comparison chart: {e}")
        return None

def extract_recommendation_info(investment_text):
    """Extract key metrics from investment recommendation text."""
    metrics = {
        'recommendation': 'HOLD',  # Default
        'expected_return': '10-15%',  # Default
        'confidence': 'Medium',  # Default
        'price_target': None,
        'position_size': 'Medium',
    }
    
    # Extract recommendation
    if "RECOMMENDATION:" in investment_text:
        rec_line = investment_text.split("RECOMMENDATION:")[1].split("\n")[0].strip()
        if "BUY" in rec_line:
            metrics['recommendation'] = "BUY"
        elif "SELL" in rec_line:
            metrics['recommendation'] = "SELL"
        elif "HOLD" in rec_line:
            metrics['recommendation'] = "HOLD"
    
    # Extract expected return
    if "EXPECTED" in investment_text and "RETURN" in investment_text:
        for line in investment_text.split("\n"):
            if "EXPECTED" in line and "RETURN" in line and ":" in line:
                return_text = line.split(":")[1].strip()
                metrics['expected_return'] = return_text
                break
    
    # Extract confidence
    if "CONFIDENCE:" in investment_text:
        conf_line = investment_text.split("CONFIDENCE:")[1].split("\n")[0].strip()
        if "High" in conf_line:
            metrics['confidence'] = "High"
        elif "Medium" in conf_line:
            metrics['confidence'] = "Medium"
        elif "Low" in conf_line:
            metrics['confidence'] = "Low"
    
    # Extract price target if available
    if "PRICE TARGET:" in investment_text:
        target_line = investment_text.split("PRICE TARGET:")[1].split("\n")[0].strip()
        metrics['price_target'] = target_line
    
    # Extract position size if available
    if "POSITION SIZE:" in investment_text or "SUGGESTED POSITION SIZE:" in investment_text:
        for line in investment_text.split("\n"):
            if ("POSITION SIZE:" in line or "SUGGESTED POSITION SIZE:" in line) and ":" in line:
                size_text = line.split(":")[1].strip()
                metrics['position_size'] = size_text
                break
    
    return metrics

def create_recommendation_summary_chart(recommendations):
    """Create a visual summary of recommendations."""
    try:
        tickers = [r['ticker'] for r in recommendations]
        rec_values = []
        colors = []
        
        # Map recommendations to numeric values and colors
        for r in recommendations:
            recommendation = r.get('metrics', {}).get('recommendation', 'HOLD')
            if recommendation == 'BUY':
                rec_values.append(1)
                colors.append(CORPORATE_COLORS['positive'])
            elif recommendation == 'SELL':
                rec_values.append(-1)
                colors.append(CORPORATE_COLORS['negative'])
            else:  # HOLD
                rec_values.append(0)
                colors.append(CORPORATE_COLORS['secondary'])
        
        # Create recommendation chart
        plt.figure(figsize=(10, 5), facecolor='white')
        plt.style.use('seaborn-v0_8-whitegrid')
        
        bars = plt.bar(tickers, rec_values, color=colors)
        
        # Add recommendation labels
        for i, r in enumerate(recommendations):
            rec = r.get('metrics', {}).get('recommendation', 'HOLD')
            plt.text(i, rec_values[i] * 0.5, rec, 
                     ha='center', va='center', color='white', fontweight='bold')
        
        plt.title("Investment Recommendations", fontsize=14, 
                  fontweight='bold', color=CORPORATE_COLORS['primary'])
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        plt.ylim(-1.5, 1.5)
        plt.grid(True, linestyle="--", alpha=0.7, color='#dddddd', axis='x')
        plt.yticks([])  # Hide y-axis ticks
        plt.tight_layout()
        
        # Save the chart
        chart_path = CHART_DIR / "recommendations_summary.png"
        plt.savefig(chart_path, dpi=150)
        plt.close()
        
        return chart_path
    except Exception as e:
        print(f"Error creating recommendation chart: {e}")
        return None

def generate_pdf_report(report_content, tickers, report_date=None, stock_analyses=None):
    """Generate a PDF report with the given content and enhanced visualizations."""
    
    if report_date is None:
        report_date = datetime.now().strftime("%Y-%m-%d")
    
    # Create a unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tickers_str = "_".join(tickers)
    if len(tickers_str) > 20:  # Limit length for filename
        tickers_str = tickers_str[:20] + "..."
    
    filename = f"SBIA_Investment_Report_{tickers_str}_{timestamp}.pdf"
    file_path = REPORT_DIR / filename
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ReportHeading',
        fontName='Helvetica-Bold',
        fontSize=18,
        spaceAfter=12,
        textColor=CORPORATE_COLORS['primary']
    ))
    styles.add(ParagraphStyle(
        name='SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=8,
        textColor=CORPORATE_COLORS['primary']
    ))
    styles.add(ParagraphStyle(
        name='SubsectionHeading',
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceAfter=6,
        textColor=CORPORATE_COLORS['secondary']
    ))
    styles.add(ParagraphStyle(
        name='StockSymbol',
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=6,
        textColor=CORPORATE_COLORS['accent']
    ))
    # Modify existing BodyText style instead of trying to add a new one
    styles['BodyText'].fontName = 'Helvetica'
    styles['BodyText'].fontSize = 10
    styles['BodyText'].spaceBefore = 4
    styles['BodyText'].spaceAfter = 4
    
    # Add table styles
    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.white
    ))
    
    # Create the document elements
    elements = []
    
    # Add logo and header
    # elements.append(Image("path/to/logo.png", width=200, height=50))  # Uncomment if you have a logo
    
    # Title
    elements.append(Paragraph(f"Sam Butler Investment Agency", styles['ReportHeading']))
    elements.append(Paragraph(f"Investment Analysis Report", styles['SectionHeading']))
    elements.append(Paragraph(f"Date: {report_date}", styles['BodyText']))
    elements.append(Paragraph(f"Tickers: {', '.join(tickers)}", styles['BodyText']))
    elements.append(Spacer(1, 24))
    
    # Parse and process the report content for clean formatting
    # Extract main sections
    sections = {}
    current_section = "Introduction"
    sections[current_section] = []
    
    for line in report_content.split('\n'):
        if line.startswith('# '):
            # Main title, already handled
            continue
        elif line.startswith('## '):
            # New section
            current_section = line.replace('## ', '').strip()
            sections[current_section] = []
        else:
            # Content for current section
            sections[current_section].append(line)
    
    # Add Executive Summary
    if "Executive Summary" in sections:
        elements.append(Paragraph("Executive Summary", styles['SectionHeading']))
        summary_text = '\n'.join(sections["Executive Summary"])
        for paragraph in summary_text.split('\n\n'):
            if paragraph.strip():
                elements.append(Paragraph(paragraph.strip(), styles['BodyText']))
        elements.append(Spacer(1, 12))
    
    # Add Market Overview
    if any(s for s in sections if "Market" in s and "Overview" in s):
        market_section = next((s for s in sections if "Market" in s and "Overview" in s), None)
        elements.append(Paragraph(market_section, styles['SectionHeading']))
        market_text = '\n'.join(sections[market_section])
        for paragraph in market_text.split('\n\n'):
            if paragraph.strip():
                elements.append(Paragraph(paragraph.strip(), styles['BodyText']))
        elements.append(Spacer(1, 12))
    
    # Generate and add comparison chart
    comparison_chart = create_performance_comparison_chart(tickers)
    if comparison_chart:
        elements.append(Paragraph("Comparative Performance", styles['SubsectionHeading']))
        elements.append(Image(str(comparison_chart), width=450, height=270))
        elements.append(Spacer(1, 12))
    
    # Process recommendations if we have the stock analyses
    if stock_analyses:
        # Extract metrics from recommendations
        for analysis in stock_analyses:
            if 'recommendation' in analysis and isinstance(analysis['recommendation'], str):
                analysis['metrics'] = extract_recommendation_info(analysis['recommendation'])
        
        # Create recommendations summary chart
        rec_chart = create_recommendation_summary_chart(stock_analyses)
        if rec_chart:
            elements.append(Paragraph("Investment Recommendations", styles['SectionHeading']))
            elements.append(Image(str(rec_chart), width=450, height=225))
            elements.append(Spacer(1, 16))
        
        # Create recommendations table
        if len(stock_analyses) > 0:
            rec_data = [["Ticker", "Recommendation", "Expected Return", "Confidence", "Position Size"]]
            for analysis in stock_analyses:
                metrics = analysis.get('metrics', {})
                rec_data.append([
                    analysis['ticker'],
                    metrics.get('recommendation', 'HOLD'),
                    metrics.get('expected_return', 'N/A'),
                    metrics.get('confidence', 'Medium'),
                    metrics.get('position_size', 'Medium')
                ])
            
            table = Table(rec_data, colWidths=[60, 100, 100, 80, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), CORPORATE_COLORS['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 20))
    
    # Add portfolio strategy
    if any(s for s in sections if "Portfolio" in s and "Strategy" in s):
        portfolio_section = next((s for s in sections if "Portfolio" in s and "Strategy" in s), None)
        elements.append(Paragraph(portfolio_section, styles['SectionHeading']))
        portfolio_text = '\n'.join(sections[portfolio_section])
        for paragraph in portfolio_text.split('\n\n'):
            if paragraph.strip():
                elements.append(Paragraph(paragraph.strip(), styles['BodyText']))
        elements.append(Spacer(1, 12))
    
    # Add individual stock analyses
    elements.append(Paragraph("Individual Stock Analyses", styles['SectionHeading']))
    elements.append(Spacer(1, 6))
    
    for ticker in tickers:
        # Start a new page for each stock
        elements.append(PageBreak())
        
        # Add stock header
        elements.append(Paragraph(f"{ticker} Analysis", styles['StockSymbol']))
        
        # Add stock chart
        chart_path = CHART_DIR / f"{ticker}_price_chart.png"
        if chart_path.exists():
            elements.append(Image(str(chart_path), width=450, height=270))
            elements.append(Spacer(1, 12))
        
        # Find the stock section in the report content
        stock_section = None
        for section_name, content in sections.items():
            if ticker in section_name:
                stock_section = section_name
                break
        
        if stock_section:
            stock_text = '\n'.join(sections[stock_section])
            for paragraph in stock_text.split('\n\n'):
                if paragraph.strip():
                    elements.append(Paragraph(paragraph.strip(), styles['BodyText']))
        else:
            # Fallback if no specific section found
            elements.append(Paragraph(f"No detailed analysis available for {ticker}.", styles['BodyText']))
    
    # Add Risk Management
    if any(s for s in sections if "Risk" in s and "Management" in s):
        elements.append(PageBreak())
        risk_section = next((s for s in sections if "Risk" in s and "Management" in s), None)
        elements.append(Paragraph(risk_section, styles['SectionHeading']))
        risk_text = '\n'.join(sections[risk_section])
        for paragraph in risk_text.split('\n\n'):
            if paragraph.strip():
                elements.append(Paragraph(paragraph.strip(), styles['BodyText']))
        elements.append(Spacer(1, 12))
    
    # Add conclusion
    if "Conclusion" in sections:
        elements.append(Paragraph("Conclusion", styles['SectionHeading']))
        conclusion_text = '\n'.join(sections["Conclusion"])
        for paragraph in conclusion_text.split('\n\n'):
            if paragraph.strip():
                elements.append(Paragraph(paragraph.strip(), styles['BodyText']))
    
    # Add a disclaimer
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Disclaimer", styles['SubsectionHeading']))
    elements.append(Paragraph(
        "This report is provided for informational purposes only and does not constitute investment advice. "
        "Past performance is not indicative of future results. Investors should conduct their own research "
        "and consult with a financial advisor before making investment decisions.",
        styles['BodyText']
    ))
    
    # Add signature
    elements.append(Spacer(1, 36))
    elements.append(Paragraph("Prepared by:", styles['BodyText']))
    elements.append(Paragraph("Sam Butler, CFA", styles['BodyText']))
    elements.append(Paragraph("Chief Investment Officer", styles['BodyText']))
    elements.append(Paragraph("Sam Butler Investment Agency", styles['BodyText']))
    
    # Build the PDF
    doc.build(elements)
    
    return file_path
