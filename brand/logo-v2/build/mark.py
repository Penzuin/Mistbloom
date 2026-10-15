"""Render the Mistbloom flower mark (same SVG as the original logo) to PNG."""
from playwright.sync_api import sync_playwright

def mark(size, p="m", halo=True):
    h = f'<circle cx="100" cy="110" r="84" fill="url(#{p}H)"/>' if halo else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 200 200">
<defs>
<radialGradient id="{p}H" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#F2C97D" stop-opacity=".32"/><stop offset="1" stop-color="#F2C97D" stop-opacity="0"/></radialGradient>
<linearGradient id="{p}C" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F1EBFF"/><stop offset="1" stop-color="#B9A5F0"/></linearGradient>
<linearGradient id="{p}S" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#C9B8F0"/><stop offset="1" stop-color="#7A64CC"/></linearGradient>
<linearGradient id="{p}O" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9D86E0"/><stop offset="1" stop-color="#4E3E9A"/></linearGradient>
</defs>
{h}
<path d="M100 72 C114 92 114 114 100 128 C86 114 86 92 100 72Z" fill="url(#{p}O)" transform="rotate(-68 100 128)"/>
<path d="M100 72 C114 92 114 114 100 128 C86 114 86 92 100 72Z" fill="url(#{p}O)" transform="rotate(68 100 128)"/>
<path d="M100 56 C117 80 117 110 100 128 C83 110 83 80 100 56Z" fill="url(#{p}S)" transform="rotate(-34 100 128)"/>
<path d="M100 56 C117 80 117 110 100 128 C83 110 83 80 100 56Z" fill="url(#{p}S)" transform="rotate(34 100 128)"/>
<path d="M100 44 C120 72 120 108 100 128 C80 108 80 72 100 44Z" fill="url(#{p}C)"/>
<circle cx="100" cy="121" r="6" fill="#F2C97D"/>
<path d="M38 146 C58 137 78 155 100 146 S142 137 162 146" fill="none" stroke="#9FB3D9" stroke-width="6" stroke-linecap="round" opacity=".85"/>
<path d="M62 162 C76 156 90 168 104 162 S128 156 140 162" fill="none" stroke="#9FB3D9" stroke-width="5" stroke-linecap="round" opacity=".5"/>
<path d="M152 34 L155 44 L165 47 L155 50 L152 60 L149 50 L139 47 L149 44Z" fill="#F2C97D"/>
</svg>'''

if __name__ == "__main__":
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, size, halo in (("mark_2000.png", 2000, True), ("mark_nohalo_2000.png", 2000, False), ("mark_64.png", 64, False), ("mark_48.png", 48, False)):
            pg = b.new_page(viewport={"width": size, "height": size})
            pg.set_content(f'<html><body style="margin:0;background:transparent">{mark(size, "m", halo)}</body></html>')
            pg.screenshot(path=name, omit_background=True)
        b.close()
    print("ok")
