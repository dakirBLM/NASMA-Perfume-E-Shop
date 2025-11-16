from modeltranslation.translator import register, TranslationOptions
from .models import Category, Collection, Product


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)


@register(Collection)
class CollectionTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)
