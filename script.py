with open('datadump.json', 'rb') as f:
    content = f.read().decode('latin-1')  # Decodifica como latin-1 (acepta ñ, tildes)

with open('datadump_fixed.json', 'w', encoding='utf-8') as f:
    f.write(content)