CATEGORIES = {
    'Maps': {},
    'Stations': {}
}


def get_nav_group_elem_ids(category):
    assert category in CATEGORIES
    return {
        'button': 'button-category-{}'.format(category),
        'collapse': 'collapse-{}'.format(category)
    }
