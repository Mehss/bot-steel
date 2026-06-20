import discord


class Paginator(discord.ui.View):
    def __init__(self, user, pages):
        super().__init__()
        self.user = user
        self.pages = pages
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.primary)
    async def previous_page(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button):
        if interaction.user != self.user:
            return

        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(
                embed=self.pages[self.current_page],
                view=self
            )

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary)
    async def next_page(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button):
        if interaction.user != self.user:
            return

        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(
                embed=self.pages[self.current_page],
                view=self
            )

    async def on_timeout(self):
        # TODO: implement delete button
        pass
