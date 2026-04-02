import pytest
from products.models import Product


@pytest.mark.django_db
def test_create_product():
    product = Product.objects.create(name="Test Product", price=19.99)
    assert product.name == "Test Product"
    assert product.price == 19.99
    assert Product.objects.count() == 1
