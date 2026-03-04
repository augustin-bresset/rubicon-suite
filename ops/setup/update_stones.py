stones = env['pdp.stone'].search([])
print(f"Checking {len(stones)} pdp.stone records.")
updated_stones = 0
for stone in stones:
    if stone.type_id and stone.shape_id and stone.shade_id and stone.size_id:
        domain = [
            ('type_id', '=', stone.type_id.id),
            ('shape_id', '=', stone.shape_id.id),
            ('shade_id', '=', stone.shade_id.id),
            ('size_id', '=', stone.size_id.id),
        ]
        weight_record = env['pdp.stone.weight'].search(domain, limit=1)
        if weight_record and stone.weight_id != weight_record:
            stone.weight_id = weight_record.id
            updated_stones += 1

print(f"Updated {updated_stones} pdp.stone records.")

pstones = env['pdp.product.stone'].search([('weight', 'in', [0.0, False])])
print(f"Found {len(pstones)} pdp.product.stone records with 0 weight.")
updated_pstones = 0
for ps in pstones:
    if ps.stone_id and ps.stone_id.weight:
        ps.weight = ps.stone_id.weight
        updated_pstones += 1

print(f"Updated {updated_pstones} pdp.product.stone records.")
env.cr.commit()
