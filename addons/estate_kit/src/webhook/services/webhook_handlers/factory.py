from typing import Any

from ....shared.services.api_client import EstateKitApiClient
from ....shared.services.api_mapper import import_from_api_data
from .activity_creator import ActivityCreator
from .approved_handler import ApprovedHandler
from .contact_request_handler import ContactRequestHandler
from .delisted_handler import DelistedHandler
from .listing_removed_handler import ListingRemovedHandler
from .new_listing_handler import NewListingHandler
from .property_data_fetcher import PropertyDataFetcher
from .property_finder import PropertyFinder
from .rejected_handler import RejectedHandler
from .service import WebhookHandlersService
from .transition_handler import TransitionHandler


class Factory:
    @staticmethod
    def create(env: Any) -> WebhookHandlersService:
        api_client = EstateKitApiClient(env)
        property_finder = PropertyFinder(env)
        activity_creator = ActivityCreator(env)
        property_data_fetcher = PropertyDataFetcher(api_client)
        transition_handler = TransitionHandler(property_finder)
        approved_handler = ApprovedHandler(property_finder)
        rejected_handler = RejectedHandler(property_finder, activity_creator)
        delisted_handler = DelistedHandler(property_finder)
        contact_request_handler = ContactRequestHandler(property_finder, activity_creator)
        new_listing_handler = NewListingHandler(property_data_fetcher, import_from_api_data, env)
        listing_removed_handler = ListingRemovedHandler(property_finder)
        return WebhookHandlersService(
            transition_handler=transition_handler,
            approved_handler=approved_handler,
            rejected_handler=rejected_handler,
            delisted_handler=delisted_handler,
            contact_request_handler=contact_request_handler,
            new_listing_handler=new_listing_handler,
            listing_removed_handler=listing_removed_handler,
        )
