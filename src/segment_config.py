"""
Unified product segment configuration for all reports.

This ensures consistency between annual and quarterly segment reports.
If a segment has no data, it should display "x" instead of being omitted.
"""

# Unified product segments per company (A-Z order)
# Combines segments from both FMP (annual) and SEC 8-K/10-Q (quarterly) sources
UNIFIED_PRODUCT_SEGMENTS = {
    'AAPL': [
        'iPhone',
        'Mac',
        'iPad',
        'Services',
        'Wearables, Home and Accessories',
    ],
    'AMD': [
        'Data Center',
        'Client',
        'Gaming',
        'Embedded',
        # Legacy segments (pre-2022)
        'Computing and Graphics',
        'Enterprise, Embedded and Semi-Custom',
        'Client and Gaming',
    ],
    'AMZN': [
        'North America',
        'International',
        'AWS',
        # Detailed segments (annual only)
        'Online Stores',
        'Third-Party Seller Services',
        'Advertising Services',
        'Subscription Services',
        'Physical Stores',
        'Amazon Web Services',
        'Other Services',
    ],
    'DELL': [
        'Infrastructure Solutions Group',
        'Client Solutions Group',
        # Legacy segments (annual 10-K)
        'Servers and networking',
        'Storage',
        'Products',
        'Services',
    ],
    'GOOGL': [
        'Google Cloud',
        'Google Services',
        # Detailed segments (annual only)
        'Google Search & Other',
        'YouTube Ads',
        'Google Subscriptions',
        'Google Network',
        'Other Bets',
    ],
    'HPQ': [
        'Personal Systems',
        'Printing',
    ],
    'META': [
        'Family of Apps',
        'Reality Labs',
    ],
    'MSFT': [
        'Intelligent Cloud',
        'Productivity and Business Processes',
        'More Personal Computing',
        # Detailed segments (annual only)
        'Server Products And Tools',
        'Microsoft Office',
        'Gaming',
        'Windows',
        'Linked In Corporation',
        'Search And News Advertising',
        'Devices',
    ],
    'MU': [
        'Cloud Memory',
        'Mobile and Client',
        'Core Data Center',
        'Automotive and Edge',
    ],
    'NVDA': [
        'Data Center',
        'Gaming',
        'Professional Visualization',
        'Automotive',
        'OEM And Other',
    ],
    'ORCL': [
        'Cloud services and license support',
        'Cloud license and on-premise license',
        'Hardware',
        'Services',
        # New segments (FY2026+)
        'Cloud',
        'Software',
        'Cloud and software',
        'Cloud and license',
    ],
    'QCOM': [
        'Handsets',
        'Automotive',
        'IoT',
        'Licensing',
    ],
    'WDC': [
        'Cloud',
        'Client',
        'Consumer',
        'Flash',
        'HDD',
    ],
}


def get_unified_segments(symbol: str) -> list:
    """Get unified product segment list for a company."""
    return UNIFIED_PRODUCT_SEGMENTS.get(symbol, [])
