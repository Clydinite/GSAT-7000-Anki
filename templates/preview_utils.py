def generate_preview_html(css_content, back_html_content):
    # This structure expects back_html_content to be a complete card
    return f"""
<!DOCTYPE html>
<html>
<head>
    <style>{css_content}</style>
</head>
<body>
    {back_html_content}
</body>
</html>
"""
