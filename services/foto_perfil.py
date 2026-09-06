"""Valida e normaliza fotos antes de armazená-las no banco."""
from io import BytesIO
import warnings

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

LIMITE_FOTO = 5 * 1024 * 1024
MAX_PIXELS = 20_000_000
FORMATOS = {"JPEG", "PNG", "WEBP"}
TIPOS = {"image/jpeg", "image/png", "image/webp"}


def normalizar_foto(conteudo: bytes, tipo: str | None) -> bytes:
    if len(conteudo) > LIMITE_FOTO:
        raise HTTPException(413, "A foto deve ter no máximo 5 MB.")
    if not conteudo or tipo not in TIPOS:
        raise HTTPException(422, "Selecione uma imagem JPG, PNG ou WebP válida.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(conteudo)) as original:
                if original.format not in FORMATOS:
                    raise ValueError("Formato não permitido")
                if original.width * original.height > MAX_PIXELS:
                    raise ValueError("Imagem muito grande")
                original.verify()
            with Image.open(BytesIO(conteudo)) as original:
                foto = ImageOps.exif_transpose(original)
                foto.thumbnail((512, 512))
                # Fundo branco para imagens transparentes e remoção de metadados.
                rgba = foto.convert("RGBA")
                limpa = Image.new("RGB", rgba.size, "white")
                limpa.paste(rgba, mask=rgba.getchannel("A"))
                saida = BytesIO()
                limpa.save(saida, format="JPEG", quality=85, optimize=True)
                return saida.getvalue()
    except (UnidentifiedImageError, OSError, ValueError,
            Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, "Imagem inválida ou muito grande. Escolha outra foto.")
