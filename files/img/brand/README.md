# Kindynos brand

| File | Use |
|---|---|
| `kindynos-mark.svg` | The square mark: avatars, favicons, small sizes |
| `kindynos-wordmark-light.svg` | The wordmark on light backgrounds |
| `kindynos-wordmark-dark.svg` | The wordmark on dark backgrounds |
| `kindynos-owl.png` | The mascot, 512 × 512, with rounded corners |
| `kindynos-social.png` | The GitHub social preview, 1280 × 640 (Settings → General → Social preview) |

The wordmark is *kindÿnos*. Its y transliterates the Greek upsilon of κίνδυνος, and ϋ is the upsilon
with a diaeresis. The two dots stand for the two main values of the causal entity axis: AI, in blue,
and human, in gold. The mark is the same ÿ on a navy tile.

## Palette

The colours come from the owl.

| Colour | Hex | Use |
|---|---|---|
| Navy | `#132747` | Text on light backgrounds, the tile of the mark |
| Gold | `#EDAA26` | The human dot |
| Cream | `#FAE5B9` | Text on dark backgrounds, the ÿ of the mark |
| Blue | `#4B70B8` on light, `#8EAEE3` on dark | The AI dot, a lighter tint of the navy |

## Type

[Fraunces](https://github.com/undercasetype/Fraunces) by Undercase Type (SIL Open Font License 1.1):
weight 600, optical size 72 and softness 50 for the wordmark, weight 400 for the tagline. The letters
are converted to paths, so the SVG files need no font.

## Mascot

The owl comes from the free library of the [IP as Logo](https://github.com/s1dashu/ip-as-logo-skill)
project ([ipaslogo.com](https://ipaslogo.com)), whose logos are free for commercial use.

## Regenerate

```bash
pip install fonttools uharfbuzz
curl -L -o Fraunces.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf"
python make_brand.py Fraunces.ttf
google-chrome --headless=new --hide-scrollbars --allow-file-access-from-files --window-size=1280,640 \
  --screenshot=kindynos-social.png social.html
```
