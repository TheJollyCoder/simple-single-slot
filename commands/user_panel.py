import discord


class UserPanelView(discord.ui.View):
    """Simple navigable user panel."""

    def __init__(self):
        super().__init__(timeout=None)
        self.page = "landing"
        self.selected_comp = None

        self.competitions = [
            {
                "name": "Screenshot Showdown",
                "description": "Post your best dino screenshot.",
                "open": True,
            },
            {
                "name": "Art Contest",
                "description": "Share your ark‑themed art.",
                "open": False,
            },
        ]

        self.submissions = {}

        self._set_landing_items()

    # ----- embed helpers -----
    def _landing_embed(self) -> discord.Embed:
        embed = discord.Embed(title="User Panel")
        embed.description = (
            "Select an option below to view competitions or your submissions."
        )
        embed.add_field(name="Competitions", value="View active competitions", inline=False)
        embed.add_field(name="My Submissions", value="View your entries", inline=False)
        return embed

    def _competitions_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Competitions")
        for idx, comp in enumerate(self.competitions, start=1):
            status = "Open" if comp.get("open") else "Closed"
            embed.add_field(
                name=f"{idx}. {comp['name']} ({status})",
                value=comp["description"],
                inline=False,
            )
        embed.set_footer(text="Select a competition below")
        return embed

    def _competition_detail_embed(self, comp) -> discord.Embed:
        embed = discord.Embed(title=comp["name"], description=comp["description"])
        status = "Open" if comp.get("open") else "Closed"
        embed.add_field(name="Status", value=status, inline=False)
        if comp.get("open"):
            embed.add_field(
                name="Submission",
                value="Upload an attachment or provide a URL using this panel",
                inline=False,
            )
        return embed

    def _submissions_embed(self) -> discord.Embed:
        embed = discord.Embed(title="My Submissions")
        if not self.submissions:
            embed.description = "You have not entered any competitions yet."
        else:
            for comp, items in self.submissions.items():
                embed.add_field(name=comp, value="\n".join(items), inline=False)
        return embed

    # ----- item builders -----
    def _set_landing_items(self):
        self.clear_items()
        self.add_item(
            discord.ui.Button(label="Competitions", style=discord.ButtonStyle.primary, custom_id="competitions")
        )
        self.add_item(
            discord.ui.Button(label="My Submissions", style=discord.ButtonStyle.primary, custom_id="submissions")
        )

    def _set_competition_items(self):
        self.clear_items()
        for idx, comp in enumerate(self.competitions):
            self.add_item(
                discord.ui.Button(
                    label=comp["name"],
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"comp_{idx}",
                )
            )
        self.add_item(discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, custom_id="back"))

    def _set_competition_detail_items(self):
        self.clear_items()
        if self.selected_comp and self.selected_comp.get("open"):
            self.add_item(
                discord.ui.Button(label="Submit URL", style=discord.ButtonStyle.success, custom_id="submit_url")
            )
            self.add_item(
                discord.ui.Button(label="Upload Attachment", style=discord.ButtonStyle.success, custom_id="submit_attach")
            )
        self.add_item(discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, custom_id="back"))

    def _set_submissions_items(self):
        self.clear_items()
        self.add_item(discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, custom_id="back"))

    # ----- view state -----
    @property
    def embed(self) -> discord.Embed:
        if self.page == "landing":
            return self._landing_embed()
        if self.page == "competitions":
            return self._competitions_embed()
        if self.page == "competition_detail" and self.selected_comp:
            return self._competition_detail_embed(self.selected_comp)
        if self.page == "submissions":
            return self._submissions_embed()
        return discord.Embed(title="User Panel")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        cid = interaction.data.get("custom_id")
        if cid == "competitions":
            self.page = "competitions"
            self._set_competition_items()
            await interaction.response.edit_message(embed=self.embed, view=self)
            return True
        if cid == "submissions":
            self.page = "submissions"
            self._set_submissions_items()
            await interaction.response.edit_message(embed=self.embed, view=self)
            return True
        if cid == "back":
            self.page = "landing"
            self.selected_comp = None
            self._set_landing_items()
            await interaction.response.edit_message(embed=self.embed, view=self)
            return True
        if cid and cid.startswith("comp_"):
            idx = int(cid.split("_")[1])
            self.selected_comp = self.competitions[idx]
            self.page = "competition_detail"
            self._set_competition_detail_items()
            await interaction.response.edit_message(embed=self.embed, view=self)
            return True
        if cid == "submit_url":
            modal = UrlSubmitModal(self)
            await interaction.response.send_modal(modal)
            return True
        if cid == "submit_attach":
            await interaction.response.send_message(
                "Please reply with your attachment.", ephemeral=True
            )
            return True
        return await super().interaction_check(interaction)


class UrlSubmitModal(discord.ui.Modal, title="Submit URL"):
    url = discord.ui.TextInput(label="Submission URL", required=True)

    def __init__(self, panel: UserPanelView):
        super().__init__()
        self.panel = panel

    async def on_submit(self, interaction: discord.Interaction):
        comp_name = self.panel.selected_comp["name"] if self.panel.selected_comp else "Unknown"
        entry = f"URL: {self.url.value}"
        self.panel.submissions.setdefault(comp_name, []).append(entry)
        await interaction.response.send_message("Submission received!", ephemeral=True)

