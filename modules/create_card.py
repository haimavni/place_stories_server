def card_data(url, img_src, title, description):
    return f"""
    <html>
        <head>
            <meta property="og:image"              content="http://{img_src}" />
            <meta property="og:image:secure_url"   content="https://{img_src}" />
            <meta property="og:image:width"        content="1200" />
            <meta property="og:image:height"       content="630" />
            <meta property="og:image:type"         content="image/jpeg" />
            <meta property="og:url"                content="https://{url}" />
            <meta property="og:type"               content="website" />
            <meta property="og:title"              content="{title}" />
            <meta property="og:description"        content="{description}" />
            <meta property="og:image:alt"          content="{img_src}" />
            <meta property="og:locale"             content="he_IL" />
            <meta charset="utf-8">
        </head>
        <body>
            <script>
                window.location="https://{url}";
            </script>
            <a href="https://{url}">{title}</a>
        </body>
    </html>"""
