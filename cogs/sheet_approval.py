from discord.ext import commands

from utils.functions import create_default_embed, try_delete


class ToBeApproved:
    def __init__(self, id: int, approvals: list, content: str, owner_id: int, channel_id: int):
        """
        :param id: ID of message
        :param approvals: List of Member ID's who approved.
        """
        self.approvals = approvals
        self.id = id
        self.owner_id = owner_id
        self.content = content
        self.channel_id = channel_id

    @classmethod
    def from_dict(cls, data):
        return cls(data['id'], data['approvals'], data['content'], data['owner_id'], data['channel_id'])

    def to_dict(self):
        return {
            'id': self.id,
            'approvals': self.approvals,
            'content': self.content,
            'owner_id': self.owner_id,
            'channel_id': self.channel_id
        }

    async def get_message(self, ctx):
        message = await ctx.guild.get_channel(self.channel_id).fetch_message(self.id)
        return message


class SheetApproval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        gid = getattr(ctx.guild, 'id', 0)
        return gid == self.bot.personal_server

    async def get_sheet(self, ctx, id):
        # Get ToBeApproved object
        db_result = await self.bot.mdb['to_approve'].find_one({'id': id})
        if db_result is None:
            await ctx.send('Could not find a sheet with Approval ID: '+str(id))
            return None
        approval = ToBeApproved.from_dict(db_result)
        # Get Owner
        sheet_owner = ctx.guild.get_member(approval.owner_id)
        if sheet_owner is None:
            await self.delete_sheet(ctx, approval)
            await ctx.send('The owner of the sheet could not be found. Deleting sheet from database...')
            return None
        return approval

    async def delete_sheet(self, ctx, sheet: ToBeApproved):
        await self.bot.mdb['to_approve'].delete_one({'id': sheet.id})
        message = await sheet.get_message(ctx)
        if message is not None:
            await try_delete(message)

    async def approve_sheet(self, ctx, sheet: ToBeApproved):
        await self.bot.mdb['to_approve'].delete_one({'id': sheet.id})
        message = await sheet.get_message(ctx)
        if message is not None:
            await SheetApproval.add_approval_fields(ctx, sheet)
            await message.add_reaction('✅')

    async def add_approval(self, ctx, sheet: ToBeApproved):
        await self.bot.mdb['to_approve'].update_one({'id': sheet.id}, {'$set': sheet.to_dict()})
        message = await sheet.get_message(ctx)
        if message is not None:
            await SheetApproval.add_approval_fields(ctx, sheet)


    @staticmethod
    async def add_approval_fields(ctx, sheet: ToBeApproved):
        message = await sheet.get_message(ctx)
        if message is not None:
            embed = message.embeds[0]
            embed.clear_fields()
            if len(sheet.approvals) < 2:
                embed.add_field(name='Approval ID', value=str(sheet.id))
            for approval in sheet.approvals:
                member = ctx.guild.get_member(approval)
                embed.add_field(name='Approval!', value=f'You have been approved by {member.display_name}')
            if len(sheet.approvals) >= 2:
                embed.add_field(name='Approved!', value=f'You have been approved! '
                                                        f'Contact a DM or Lord of the Sheet for more information.',
                                inline=False)
            await message.edit(embed=embed)

    async def remove_approval(self, ctx, sheet: ToBeApproved):
        message = await sheet.get_message(ctx)
        if ctx.author.id in sheet.approvals:
            sheet.approvals.remove(ctx.author.id)
            await self.bot.mdb['to_approve'].update_one({'id': sheet.id}, {'$set': sheet.to_dict()})
        if message is not None:
            await SheetApproval.add_approval_fields(ctx, sheet)

    @commands.command(name='sheet')
    async def submit_sheet(self, ctx, *, content: str):
        """
        Sends a request for a sheet to be approved.
        """

        # Send Embed
        embed = create_default_embed(ctx)
        embed.title = f'Sheet Approval - {ctx.author.display_name}'
        embed.description = content
        message = await ctx.send(embed=embed)

        # Create ToBeApproved object
        new_approval = ToBeApproved(message.id, [], content, ctx.author.id, ctx.channel.id)
        await self.bot.mdb['to_approve'].insert_one(new_approval.to_dict())

        # Edit Message with Approval ID
        embed.add_field(name='Approval ID', value=str(message.id))
        await message.edit(embed=embed)
        return

    @commands.command(name='approve')
    @commands.has_any_role('DM', 'Lord of the Sheet')
    async def approve_sheet_command(self, ctx, to_approve: int):
        """
        Adds an approval to a sheet
        You must add the message ID as an argument.
        """

        # Get ToBeApproved object
        approval: ToBeApproved = await self.get_sheet(ctx, to_approve)
        if approval is None:
            return
        sheet_owner = ctx.guild.get_member(approval.owner_id)
        # Sanity Checks
        if ctx.author.id in approval.approvals:
            return await ctx.send('You have already approved this sheet! You cannot approve it again.')
        if ctx.author.id == approval.owner_id:
            return await ctx.send('You cannot approve your own sheet!')
        # Approve
        approval.approvals.append(ctx.author.id)
        if len(approval.approvals) >= 2:
            await self.approve_sheet(ctx, approval)
            return await ctx.send(f'Sheet has been fully approved! '
                                  f'Contact the Sheet Owner ({sheet_owner.mention}) with approval details.')
        else:
            await self.add_approval(ctx, approval)
            return await ctx.send('You have added your approval to the sheet!')

    @commands.command(name='deny')
    @commands.has_any_role('DM', 'Lord of the Sheet')
    async def deny_sheet_command(self, ctx, to_deny: int):
        """
        Removes an approval from a sheet.
        Must specify the sheet id as an argument.
        """
        sheet: ToBeApproved = await self.get_sheet(ctx, to_deny)
        if sheet is None:
            return
        if ctx.author.id not in sheet.approvals:
            return await ctx.send('You have not approved this sheet, so you cannot remove your approval.')
        await self.remove_approval(ctx, sheet)
        return await ctx.send('You have removed your approval from Sheet ID: '+str(sheet.id))


def setup(bot):
    bot.add_cog(SheetApproval(bot))
