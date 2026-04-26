def calculate_metrics(clicks, impressions, conversions, spend, revenue):
    """Calculate key ad campaign performance metrics."""

    # Avoid division by zero
    impressions = max(impressions, 1)
    clicks = max(clicks, 1)
    spend = max(spend, 0.01)

    ctr = round((clicks / impressions) * 100, 2)
    conversion_rate = round((conversions / clicks) * 100, 2)
    roi = round(((revenue - spend) / spend) * 100, 2)
    cpc = round(spend / clicks, 2)         # cost per click
    cpa = round(spend / max(conversions, 1), 2)  # cost per acquisition
    roas = round(revenue / spend, 2)        # return on ad spend

    # Performance ratings
    def rate(value, good, great):
        if value >= great:
            return ('Excellent', '#3fb950')
        if value >= good:
            return ('Good',      '#d29922')
        return ('Needs Work',  '#f85149')

    ctr_rating = rate(ctr,             1.0,  3.0)
    conv_rating = rate(conversion_rate, 2.0,  5.0)
    roi_rating = rate(roi,            20.0, 50.0)

    # Optimization suggestions
    suggestions = []

    if ctr < 1.0:
        suggestions.append({
            'icon': '🎯',
            'title': 'Improve Ad Copy',
            'text': f'Your CTR is {ctr}% (below 1%). Try stronger headlines and clear call-to-actions.'
        })
    if conversion_rate < 2.0:
        suggestions.append({
            'icon': '🛒',
            'title': 'Optimize Landing Page',
            'text': f'Conversion rate is {conversion_rate}%. Simplify your landing page and reduce friction.'
        })
    if roi < 0:
        suggestions.append({
            'icon': '💰',
            'title': 'Review Budget Allocation',
            'text': f'ROI is negative ({roi}%). Reduce spend on underperforming segments.'
        })
    if cpc > 2.0:
        suggestions.append({
            'icon': '📉',
            'title': 'Reduce Cost Per Click',
            'text': f'CPC is ${cpc}. Use more specific audience targeting to lower costs.'
        })
    if not suggestions:
        suggestions.append({
            'icon': '🚀',
            'title': 'Campaign Performing Well',
            'text': 'All key metrics are within healthy ranges. Consider scaling the budget.'
        })

    return {
        'ctr': ctr,
        'conversion_rate': conversion_rate,
        'roi': roi,
        'cpc': cpc,
        'cpa': cpa,
        'roas': roas,
        'clicks': int(clicks),
        'impressions': int(impressions),
        'conversions': int(conversions),
        'spend': round(spend, 2),
        'revenue': round(revenue, 2),
        'profit': round(revenue - spend, 2),
        'ctr_rating': ctr_rating,
        'conv_rating': conv_rating,
        'roi_rating': roi_rating,
        'suggestions': suggestions,
    }
