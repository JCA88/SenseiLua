# SenseiLua

SenseiLua est un petit outil d'analyse statique conçu pour aider les
apprenants de Lua à repérer rapidement quelques erreurs fréquentes :
indentation incohérente, espaces en fin de ligne et blocs mal fermés. Il ne se
substitue pas à un analyseur complet mais fournit un retour rapide et clair.

## Installation

```bash
pip install -e .[dev]
```

## Utilisation

Analysez un ou plusieurs fichiers Lua :

```bash
python -m sensei_lua script.lua
```

Options utiles :

- `--indent-size` pour ajuster la largeur d'indentation attendue (4 par défaut).
- `--allow-tabs` pour autoriser les tabulations en début de ligne.
- `--color` pour colorer la sortie.

## Tests

```bash
pytest
```
