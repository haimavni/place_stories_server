def card_data(url, img_src, title, description):
    return f"""
    <html>
        <head>
            <meta property="og:url"                content="https://{url}" />
            <meta property="og:type"               content="website" />
            <meta property="og:title"              content="{title}" />
            <meta property="og:description"        content="{description}" />
            <meta property="og:image"              content="{img_src}" />
        </head>
        <body>
            <script>
                window.location="https://{url}";
            </script>
        </body>
    </html>"""
