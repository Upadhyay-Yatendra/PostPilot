from langchain.prompts import PromptTemplate

post_prompt_template = PromptTemplate(
    input_variables=["prompt", "topic", "tone", "length", "audience", "style_sample", "trending_sample"],
    template=(
        "Generate a LinkedIn post: {prompt}\n"
        "Topic: {topic}. "
        "Tone: {tone}. "
        "Length: {length}. "
        "Target audience: {audience}.\n"
        "Match this style: {style_sample}\n"
        "Reference or take inspiration from this trending post: {trending_sample}\n"
        "Return only the final post text."
    )
)

def build_prompt(
    prompt, topic=None, tone=None, length=None, audience=None, style_sample=None, trending_sample=None
):
    # Fill defaults with empty strings to avoid None in prompt
    prompt_vals = {
        "prompt": prompt or "",
        "topic": topic or "",
        "tone": tone or "",
        "length": length or "",
        "audience": audience or "",
        "style_sample": style_sample or "",
        "trending_sample": trending_sample or ""
    }
    return post_prompt_template.format(**prompt_vals)
