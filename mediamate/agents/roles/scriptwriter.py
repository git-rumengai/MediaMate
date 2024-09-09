import asyncio
from pathlib import Path
from pydantic import BaseModel
from mediamate.agents.actions.copywriting import Copywriting, create_response_model
from mediamate.utils.llm_pydantic import llm_pydantic

from metagpt.actions import CollectLinks, WebBrowseAndSummarize
from metagpt.const import RESEARCH_PATH
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message


class Report(BaseModel):
    topic: str
    links: dict[str, list[str]] = None
    summaries: list[tuple[str, str]] = None
    content: str = ""


class Scriptwriter(Role):
    name: str = 'RuMengAI'
    profile: str = 'Scriptwriter'
    goal: str = 'Creating scripts specifically for YouTube videos'
    constraints: str = "Ensure clarity, logical structure, and simplicity in language"
    language: str = "zh-cn"
    enable_concurrency: bool = True
    content_length: int = 300
    save_path: str = ''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CollectLinks, WebBrowseAndSummarize, Copywriting])
        self._set_react_mode(RoleReactMode.BY_ORDER.value, len(self.actions))
        if self.language not in ("en-us", "zh-cn"):
            logger.warning(f"The language `{self.language}` has not been tested, it may not work.")

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        msg = self.rc.memory.get(k=1)[0]
        if isinstance(msg.instruct_content, Report):
            instruct_content = msg.instruct_content
            topic = instruct_content.topic
        else:
            instruct_content = None
            topic = msg.content

        script_system_text = f'You are an AI scriptwriter, and your script topic is:\n#TOPIC#\n{topic}. Please respond in {self.language}.'
        if isinstance(todo, CollectLinks):
            links = await todo.run(topic, 3, 3)
            ret = Message(
                content="", instruct_content=Report(topic=topic, links=links), role=self.profile, cause_by=todo
            )
        elif isinstance(todo, WebBrowseAndSummarize):
            links = instruct_content.links
            todos = (
                todo.run(*url, query=query, system_text=script_system_text) for (query, url) in links.items() if url
            )
            if self.enable_concurrency:
                summaries = await asyncio.gather(*todos)
            else:
                summaries = [await i for i in todos]
            summaries = list((url, summary) for i in summaries for (url, summary) in i.items() if summary)
            ret = Message(
                content="", instruct_content=Report(topic=topic, summaries=summaries), role=self.profile, cause_by=todo
            )
        else:
            summaries = instruct_content.summaries
            summary_text = "\n---\n".join(f"url: {url}\nsummary: {summary}" for (url, summary) in summaries)
            content = await self.rc.todo.run(topic, summary_text, min_length_content=self.content_length, system_text=script_system_text)
            ret = Message(
                content="",
                instruct_content=Report(topic=topic, content=content),
                role=self.profile,
                cause_by=self.rc.todo,
            )
        self.rc.memory.add(ret)
        return ret

    async def react(self) -> Message:
        msg = await super().react()
        report = msg.instruct_content
        self.write_report(report.topic, report.content)
        return msg

    def write_report(self, topic, ai_response: str):
        ResponseModel = create_response_model(min_length_content=self.content_length)
        response = llm_pydantic.get_response_model(ai_response, ResponseModel)
        if self.save_path:
            filepath = Path(self.save_path)
        else:
            filepath = RESEARCH_PATH
        if not filepath.exists():
            filepath.mkdir(parents=True)
        filename = filepath / f'{topic}.txt'
        filename.write_text(f'{response.title}\n\n{response.content}', encoding='utf-8')
