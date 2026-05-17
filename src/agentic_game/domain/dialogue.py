from __future__ import annotations

from enum import StrEnum


class DialoguePhase(StrEnum):
    GREETING = "greeting"
    CHOICE = "choice"
    REACT = "react"
    REWARD = "reward"
    END = "end"


class DialogueEvent(StrEnum):
    CONTINUE = "continue"
    ASK_RUMOR = "ask_rumor"
    ASK_TRADE = "ask_trade"
    THANK = "thank"
    LEAVE = "leave"
    CLAIM_REWARD = "claim_reward"
