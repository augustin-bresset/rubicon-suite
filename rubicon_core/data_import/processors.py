from ..models.reference import StoneCategory, StoneType



def process_stone_type(row: dict, session):
    """
    row: {'code': 'ABA', 'name': 'Abalone', 'category_code': 'H', 'relative_density': '1.00'}
    session: SQLAlchemy Session, pour faire des requêtes auxiliaires.
    The density is calculate relatively of the quartz, the stone of reference.
    It is mainly used as a reference because it have the lowest variability.
    Its density is 2.655 +/- 0.0005g/cm3
    """
    density_reference = 2.655
    cat_code = row.get('category_code')
    if not cat_code:
        return None
    category = session.query(StoneCategory).filter_by(code=row['category_code']).one()
    absolute_density = float(row['relative_density'] or 1) * density_reference
    return StoneType(
        code        = row['code'].strip(),
        name        = row['name'].strip(),
        density     = absolute_density,
        category_id = category.id
    )

        


