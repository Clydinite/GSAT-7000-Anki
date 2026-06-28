def generate_preview_html(flashcard_content, css_content, back_html_content):
    # This logic combines the card content, css and back.html structure
    return f"""
<!DOCTYPE html>
<html>
<head>
    <style>{css_content}</style>
</head>
<body>
    <div class="card">{flashcard_content}</div>
    {back_html_content}
</body>
</html>
"""
