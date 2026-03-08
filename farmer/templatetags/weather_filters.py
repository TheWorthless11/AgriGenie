from django import template

register = template.Library()


@register.filter
def weather_icon(description):
    """Map weather description to a Font Awesome icon name."""
    if not description:
        return 'cloud-sun'
    desc = description.lower()
    if 'sunny' in desc or 'clear' in desc:
        return 'sun'
    elif 'rain' in desc or 'drizzle' in desc or 'shower' in desc:
        return 'cloud-rain'
    elif 'thunder' in desc or 'storm' in desc:
        return 'bolt'
    elif 'snow' in desc or 'sleet' in desc:
        return 'snowflake'
    elif 'fog' in desc or 'mist' in desc or 'haze' in desc:
        return 'smog'
    elif 'cloud' in desc or 'overcast' in desc:
        return 'cloud'
    elif 'wind' in desc:
        return 'wind'
    elif 'partly' in desc:
        return 'cloud-sun'
    return 'cloud-sun'
