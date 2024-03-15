import logging
from typing import Union, Literal

import openai
from pydantic import BaseModel, Field


def prompt_template(input_text: str, chunks: list[str]):
    return f"""
    Begin your engagement, This is my input text:
    {input_text}
    ---
    Below is the context
    ---
    {", ".join(chunks)}
    ---
    Answer the question based on the context.
    """


def summary_template(old_summary: str, new_info: str):
    if not old_summary:
        return f"""
        summarizing the user grievance:
        ---
        {new_info}
        """
    return f"""
    the below is the old summary:
    ---
    {old_summary}
    ---
    Update the summary with new information:
    ---
    {new_info}
    """


class OpenAIChatAgent:
    ANYSCALE_API_KEY: str
    OPENAI_API_KEY: str
    OPENAI_URI: str = "https://api.openai.com/v1"
    ANYSCALE_URI: str = "https://api.endpoints.anyscale.com/v1"

    SystemPrompt: str = """
    You are an helpful code assistant.
    """

    SummaryPrompt: str = """
    ...
    """

    def __init__(self, model: str):
        self.message_history = [
            {
                "role": "system",
                "content": self.SystemPrompt
            },
        ]
        self.model = model
        self._client: Union["openai.OpenAI", None] = None
        self.use_backup = False

    def __enter__(self):
        self._client = openai.OpenAI(
            base_url=self.ANYSCALE_URI if not self.use_backup else self.OPENAI_URI,
            api_key=self.ANYSCALE_API_KEY if not self.use_backup else self.OPENAI_API_KEY
        )
        self._old_model = self.model
        if self.use_backup: self.model = "gpt-3.5-turbo"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.close()
        self._client = None
        self.model = self._old_model
        self.use_backup = False

    def __call__(self, use_backup: bool = False):
        self.use_backup = use_backup
        return self

    def update_message_history(self, content, role):
        self.message_history.append({
            'role': role,
            'content': content
        })

    def respond(self, input_text: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[*self.message_history, {"role": "user", "content": input_text}],
            temperature=0.7,
        )
        logging.info(response)
        assistant_response = response.choices[0].message.content
        self.update_message_history(input_text, 'user')
        self.update_message_history(assistant_response, 'assistant')
        return assistant_response

    class Summary(BaseModel):
        summary: str
        title: str

    def get_summary(self, text: str, old_summary: str, agent_summary: str) -> "Summary":
        chat_completion = self._client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.1",
            response_format={  # noqa
                "type": "json_object",
                "schema": self.Summary.model_json_schema()
            },
            messages=[
                {"role": "system", "content": self.SummaryPrompt},
                {"role": "user", "content": old_summary},
                {"role": "assistant", "content": "ok now give the new information to update the summary"},
                # {"role": "assistant", "content": agent_summary},
                {"role": "user", "content": f"Here is the new information: {text}"}
            ],
            temperature=0.6,
            max_tokens=256,
            seed=1234,
        )
        json_msg = chat_completion.choices[0].message.content
        try:
            eval(json_msg)
        except SyntaxError:
            json_msg += "}"
        return self.Summary.parse_obj(eval(json_msg))
