# Ee's Wardrobe

A touch-first, Clueless-inspired wardrobe carousel made from your own clothes.

The built-in closet includes black and pink T-shirts, white and green
singlets, a blue shirt, a yellow plaid top, blue and black jeans, skirts, and
shorts. The fitting-room background is deliberately mid-tone so both light
and dark clothes remain visible.

## Add clothes from a phone

1. Open CHER CLOSET on the Cyberdeck.
2. Connect the phone to the same Wi-Fi or hotspot as the Cyberdeck.
3. Open `http://cyberdeck3.local:8765` in the phone browser.
4. Choose Tops or Bottoms, select several photos, and tap **Add to Closet**.

The phone converts photos into small PPM images before upload, so ordinary
iPhone and Android photos do not require extra image software on the Pi. For
the cleanest automatic cut-out, photograph one item at a time on a plain,
contrasting background.

Photos stay in `~/cyberdeck-wardrobe/tops` and
`~/cyberdeck-wardrobe/bottoms`. Files can also be copied into those folders
over SSH. Tap the upper arrows to browse tops, the lower arrows to browse
bottoms, and **Dress Me** to preview and save the outfit.

Tap **Dress Me** to see one clean, full-body pixel avatar wearing the selected
top and bottom. The avatar uses a friendly pixel-art face and does not use a
personal photograph.
