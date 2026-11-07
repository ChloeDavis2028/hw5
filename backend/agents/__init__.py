"""The five agents on the Campus Customs team, by role, plus the Flight Instructor (learning)."""
from agents.accounting import agent as accounting
from agents.boss import agent as boss
from agents.customer_service import agent as customer_service
from agents.facilities import agent as facilities
from agents.inventory import agent as inventory
from agents.learning import agent as learning

AGENTS = {
    "boss": boss,
    "inventory": inventory,
    "accounting": accounting,
    "facilities": facilities,
    "customer_service": customer_service,
    "learning": learning,  # not a ticket crew member: ask_teammate cannot reach it
}
