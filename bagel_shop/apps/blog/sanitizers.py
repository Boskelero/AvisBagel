import nh3


ALLOWED_TAGS = {
    "a", "blockquote", "br", "caption", "code", "em", "figcaption", "figure",
    "h2", "h3", "h4", "hr", "i", "img", "li", "ol", "p", "pre", "s",
    "strong", "sub", "sup", "table", "tbody", "td", "th", "thead", "tr", "u", "ul",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "target", "title"},
    "img": {"alt", "height", "src", "width"},
    "figure": {"class"},
    "figcaption": {"class"},
    "table": {"class"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan", "scope"},
}


def sanitize_article_html(value):
    if not value:
        return ""
    return nh3.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto", "tel"},
        link_rel="noopener noreferrer",
    )
