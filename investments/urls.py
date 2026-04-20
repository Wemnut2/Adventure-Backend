# investments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InvestmentPlanViewSet, UserInvestmentViewSet, InvestmentTransactionViewSet
)

router = DefaultRouter()
router.register('plans', InvestmentPlanViewSet, basename='investment-plan')
router.register('investments', UserInvestmentViewSet, basename='user-investment')
router.register('transactions', InvestmentTransactionViewSet, basename='investment-transaction')

urlpatterns = [
    path('', include(router.urls)),
]# investments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InvestmentPlanViewSet, 
    UserInvestmentViewSet, 
    InvestmentTransactionViewSet
)

router = DefaultRouter()
router.register('plans', InvestmentPlanViewSet, basename='investment-plan')
router.register('investments', UserInvestmentViewSet, basename='user-investment')
router.register('transactions', InvestmentTransactionViewSet, basename='investment-transaction')

urlpatterns = [
    path('', include(router.urls)),
]