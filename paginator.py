import discord
from discord.ui import View, Button

class EmbedPaginator(View):
    def __init__(self, text: str, title: str = "", color: int = 0x00ff00, chunk_size: int = 4000):
        super().__init__(timeout=None)  # You can set a timeout if you want
        self.chunk_size = chunk_size
        self.pages = self.split_text(text, chunk_size)
        self.index = 0
        self.title = title
        self.color = color

        # Disable buttons if only 1 page
        if len(self.pages) <= 1:
            self.prev_button.disabled = True
            self.next_button.disabled = True

    def split_text(self, text: str, size: int):
        """Split text into chunks."""
        return [text[i:i+size] for i in range(0, len(text), size)]

    @property
    def prev_button(self):
        return self.children[0]

    @property
    def next_button(self):
        return self.children[1]

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: Button):
        self.index = (self.index - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: Button):
        self.index = (self.index + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.get_embed())

    def get_embed(self):
        embed = discord.Embed(
            title=f"{self.title} (Page {self.index+1}/{len(self.pages)})" if self.title else f"Page {self.index+1}/{len(self.pages)}",
            description=self.pages[self.index],
            color=self.color
        )
        return embed

    async def start(self, ctx_or_channel):
        embed = self.get_embed()
        if isinstance(ctx_or_channel, discord.Interaction):
            if ctx_or_channel.response.is_done():
                # já respondeu ou deferiu
                await ctx_or_channel.followup.send(embed=embed, view=self)
            else:
                await ctx_or_channel.response.send_message(embed=embed, view=self)
        else:
            await ctx_or_channel.send(embed=embed, view=self)
