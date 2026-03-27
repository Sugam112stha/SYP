from django.urls import path
from . import views

urlpatterns = [
    # ── Public ────────────────────────────────────────────────
    path('',                      views.index,            name='index'),
    path('products/',             views.products_view,    name='products'),
    path('products/<int:pk>/',    views.product_detail,   name='product_detail'),
    path('categories/',           views.categories_view,  name='categories'),
    path('deals/',                views.deals,            name='deals'),
    path('about/',                views.about,            name='about'),
    path('contact/',              views.contact,          name='contact'),
    path('faq/',                  views.faq,              name='faq'),
    path('terms/',                views.terms,            name='terms'),

    # ── Auth ──────────────────────────────────────────────────
    path('register/',             views.register_view,        name='register'),
    path('login/',                views.login_view,           name='login'),
    path('logout/',               views.logout_view,          name='logout'),
    path('verify-email/<str:token>/', views.verify_email,     name='verify_email'),
    path('resend-verification/',  views.resend_verification,  name='resend_verification'),

    # ── Protected ─────────────────────────────────────────────
    path('dashboard/',            views.dashboard,        name='dashboard'),
    path('sell/',                 views.sell,             name='sell'),
    path('cart/',                 views.cart_view,        name='cart'),
    path('cart/add/<int:pk>/',    views.add_to_cart,      name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/',             views.checkout,         name='checkout'),

    # ── Payment ───────────────────────────────────────────────
    # Called when user cancels eSewa or Khalti — restores items to cart
    path('payment-cancelled/',    views.payment_cancelled, name='payment_cancelled'),

    # ── Messages ──────────────────────────────────────────────
    path('messages/',                                               views.messages_view,  name='messages'),
    path('messages/send/<int:product_pk>/',                         views.send_message,   name='send_message'),
    path('messages/reply/<int:product_pk>/<int:buyer_pk>/',         views.seller_reply,   name='seller_reply'),
    path('messages/conversation/<int:product_pk>/<int:other_pk>/',  views.conversation,   name='conversation'),

    # ── Other ─────────────────────────────────────────────────
    path('complaints/',              views.complaints_view,  name='complaints'),
    path('payout/request/',          views.request_payout,   name='request_payout'),
    path('product/delete/<int:pk>/', views.delete_product,   name='delete_product'),
    path('profile/update/',          views.update_profile,   name='update_profile'),
    path('profile/toggle-role/',     views.toggle_role,      name='toggle_role'),
]