def card_data(url, img_src, width, height, title, description):
    return f"""
    <html>
        <head>
            <meta property="og:url"                content="https://{url}" />
            <meta property="og:type"               content="website" />
            <meta property="og:title"              content="{title}" />
            <meta property="og:description"        content="{description}" />
            <meta property="og:image"              content="{img_src}" />
            <meta property="og:image:width"        content="{width}" />
            <meta property="og:image:height"       content="{height}" />
            <meta property="og:locale"             content="he_IL" />
        </head>
        <body>
            <script>
                window.location="https://{url}";
            </script>
        </body>
    </html>"""
