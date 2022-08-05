def card_data(url, img_src, title, description):
    return f"""
    <html>
        <head>
            <meta property="og:url"                content="https://{url}" />
            <meta property="og:type"               content="website" />
            <meta property="og:title"              content="{title}" />
            <meta property="og:description"        content="{description}" />
            <meta property="og:image"              content="{img_src}" />
            <meta property="og:image:type"         content="image/jpeg" />
            <meta property="og:image:width"        content="800" />
            <meta property="og:image:height"       content="420" />
            <meta property="og:locale"             content="he_IL" />
        </head>
        <body>
            <script>
                window.location="https://{url}";
            </script>
            <a href="https://{url}">{title}</a>
        </body>
    </html>"""
