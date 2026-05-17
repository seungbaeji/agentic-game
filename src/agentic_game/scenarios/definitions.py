"""ScenarioSpec definitions for each supported game scenario."""

from __future__ import annotations

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.domain.dialogue import DialogueEvent, DialoguePhase
from agentic_game.domain.exploration import ExplorationEvent, ExplorationPhase
from agentic_game.domain.quest import QuestEvent, QuestPhase
from agentic_game.domain.skill_training import SkillTrainingEvent, SkillTrainingPhase
from agentic_game.domain.trade import TradeEvent, TradePhase
from agentic_game.flow.battle import BATTLE_TRANSITIONS
from agentic_game.flow.craft import CRAFT_TRANSITIONS
from agentic_game.flow.dialogue import DIALOGUE_TRANSITIONS
from agentic_game.flow.exploration import EXPLORATION_TRANSITIONS
from agentic_game.flow.quest import QUEST_TRANSITIONS
from agentic_game.flow.skill_training import SKILL_TRAINING_TRANSITIONS
from agentic_game.flow.trade import TRADE_TRANSITIONS
from agentic_game.scenarios.spec import ScenarioNode, ScenarioSpec

BATTLE_SCENARIO = ScenarioSpec[BattlePhase, BattleEvent](
    name="battle",
    initial_phase=BattlePhase.PREPARE,
    transitions=BATTLE_TRANSITIONS,
    phase_to_node={
        BattlePhase.ACTION: ScenarioNode.HITL,
        BattlePhase.RESOLVE: ScenarioNode.EXECUTE,
        BattlePhase.COMPLETE: ScenarioNode.RESPONSE,
    },
    terminal_phases=(BattlePhase.COMPLETE,),
)

CRAFT_SCENARIO = ScenarioSpec[CraftPhase, CraftEvent](
    name="craft",
    initial_phase=CraftPhase.SELECT_RECIPE,
    transitions=CRAFT_TRANSITIONS,
    phase_to_node={
        CraftPhase.CRAFT: ScenarioNode.HITL,
        CraftPhase.RESULT: ScenarioNode.EXECUTE,
        CraftPhase.COMPLETE: ScenarioNode.RESPONSE,
    },
    terminal_phases=(CraftPhase.COMPLETE,),
)

EXPLORATION_SCENARIO = ScenarioSpec[ExplorationPhase, ExplorationEvent](
    name="exploration",
    initial_phase=ExplorationPhase.START,
    transitions=EXPLORATION_TRANSITIONS,
    phase_to_node={
        ExplorationPhase.CHOOSE_PATH: ScenarioNode.HITL,
        ExplorationPhase.ENCOUNTER: ScenarioNode.EXECUTE,
        ExplorationPhase.DISCOVER: ScenarioNode.RESPONSE,
        ExplorationPhase.COMPLETE: ScenarioNode.RESPONSE,
    },
    terminal_phases=(ExplorationPhase.COMPLETE,),
)

QUEST_SCENARIO = ScenarioSpec[QuestPhase, QuestEvent](
    name="quest",
    initial_phase=QuestPhase.AVAILABLE,
    transitions=QUEST_TRANSITIONS,
    phase_to_node={
        QuestPhase.ACCEPTED: ScenarioNode.HITL,
        QuestPhase.IN_PROGRESS: ScenarioNode.EXECUTE,
        QuestPhase.TURN_IN: ScenarioNode.RESPONSE,
        QuestPhase.COMPLETE: ScenarioNode.RESPONSE,
        QuestPhase.FAILED: ScenarioNode.RESPONSE,
    },
    terminal_phases=(QuestPhase.COMPLETE, QuestPhase.FAILED),
)

TRADE_SCENARIO = ScenarioSpec[TradePhase, TradeEvent](
    name="trade",
    initial_phase=TradePhase.BROWSE,
    transitions=TRADE_TRANSITIONS,
    phase_to_node={
        TradePhase.NEGOTIATE: ScenarioNode.HITL,
        TradePhase.CONFIRM: ScenarioNode.RESPONSE,
        TradePhase.EXCHANGE: ScenarioNode.EXECUTE,
        TradePhase.COMPLETE: ScenarioNode.RESPONSE,
        TradePhase.CANCELLED: ScenarioNode.RESPONSE,
    },
    terminal_phases=(TradePhase.COMPLETE, TradePhase.CANCELLED),
)

DIALOGUE_SCENARIO = ScenarioSpec[DialoguePhase, DialogueEvent](
    name="dialogue",
    initial_phase=DialoguePhase.GREETING,
    transitions=DIALOGUE_TRANSITIONS,
    phase_to_node={
        DialoguePhase.CHOICE: ScenarioNode.HITL,
        DialoguePhase.REACT: ScenarioNode.RESPONSE,
        DialoguePhase.REWARD: ScenarioNode.RESPONSE,
        DialoguePhase.END: ScenarioNode.RESPONSE,
    },
    terminal_phases=(DialoguePhase.END,),
)

SKILL_TRAINING_SCENARIO = ScenarioSpec[SkillTrainingPhase, SkillTrainingEvent](
    name="skill_training",
    initial_phase=SkillTrainingPhase.SELECT_SKILL,
    transitions=SKILL_TRAINING_TRANSITIONS,
    phase_to_node={
        SkillTrainingPhase.TRAIN: ScenarioNode.RESPONSE,
        SkillTrainingPhase.RESOLVE: ScenarioNode.EXECUTE,
        SkillTrainingPhase.LEVEL_UP: ScenarioNode.RESPONSE,
        SkillTrainingPhase.COMPLETE: ScenarioNode.RESPONSE,
    },
    terminal_phases=(SkillTrainingPhase.COMPLETE,),
)
