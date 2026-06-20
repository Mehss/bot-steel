import discord
import constant


class SelectionView(discord.ui.View):
    def __init__(self, user: discord.User, generate_callback: callable):
        super().__init__(timeout=60)
        self.user = user
        self.generate_callback = generate_callback
        self.difficulty = None
        self.party_level = None
        self.chara_count = None
        self.monster_role = constant.MONSTER_ROLE_LIST

    @discord.ui.select(
        placeholder="Select Party Level",
        options=[discord.SelectOption(
            label=str(i), value=str(i),
            description=f"Level {i}") for i in range(1, 15)]
    )
    async def party_level_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "This UI is not for you!", ephemeral=True
            )
        self.party_level = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        placeholder="Select Character Count",
        options=[discord.SelectOption(
            label=str(i), value=str(i),
            description=f"{i} character.") for i in range(1, 15)]
    )
    async def chara_count_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "This UI is not for you!", ephemeral=True
            )
        self.chara_count = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        placeholder="Select Difficulty",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Easy", value="easy"),
            discord.SelectOption(label="Normal", value="normal"),
            discord.SelectOption(label="Hard", value="hard"),
            discord.SelectOption(label="Custom", value="custom",
                                 description="Define XP along with keywords."),
        ]
    )
    async def diff_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "This UI is not for you!", ephemeral=True
            )
        self.difficulty = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        placeholder="Select Monster Role",
        min_values=1,
        max_values=len(constant.MONSTER_ROLE_LIST),
        options=[
            discord.SelectOption(label=role, value=role, default=True)
            for role in constant.MONSTER_ROLE_LIST
        ]
    )
    async def monster_role_callback(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "This UI is not for you!", ephemeral=True
            )
        self.monster_role = select.values
        await interaction.response.defer()

    @discord.ui.button(
        label="Submit", style=discord.ButtonStyle.green
    )
    async def submit_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "This UI is not for you!", ephemeral=True
            )

        if (
            self.party_level is None or
            self.chara_count is None or
            self.difficulty is None or
            self.monster_role is None
        ):
            return await interaction.response.edit_message(
                content="No values selected! Deleting...",
                view=None,
                delete_after=2,
            )

        await interaction.response.edit_message(
            content="Success. Deleting...",
            view=None,
            delete_after=2,
        )

        await self.generate_callback(
            int(self.party_level),
            int(self.chara_count),
            self.difficulty,
            self.monster_role,
            interaction
        )
