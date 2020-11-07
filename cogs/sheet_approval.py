from discord.ext import commands
import discord
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
        gid = getattr(ctx.guild, 'id', None)
        return ctx.guild.id == self.bot.my_server_id

    async def delete_sheet(self, ctx, sheet: ToBeApproved):
        await self.bot.mdb['to_approve'].delete_one({'id': sheet.id})
        message = await sheet.get_message(ctx)
        if message is not None:
            await try_delete(message)

    async def approve_sheet(self, ctx, sheet: ToBeApproved):
        await self.bot.mdb['to_approve'].delete_one({'id': sheet.id})
        message = await sheet.get_message(ctx)
        if message is not None:
            await message.add_reaction('✅')

    async def add_approval(self, ctx, sheet: ToBeApproved):
        message = await sheet.get_message(ctx)
        if message is not None:
            embed = message.embeds[0]
            embed.add_field(name=f'Approved By: {ctx.author.display_name}',
                            value='Note, this does not mean you are fully approved, wait for the check mark reaction.')
            await message.edit(embed=embed)

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
        """

        # Get ToBeApproved object
        db_result = await self.bot.mdb['to_approve'].find_one({'id': to_approve})
        if db_result is None:
            await ctx.send('Could not find a sheet with Approval ID: '+str(to_approve))
        approval = ToBeApproved.from_dict(db_result)
        # Get Owner
        sheet_owner = ctx.guild.get_member(approval.owner_id)
        if sheet_owner is None:
            await self.delete_sheet(ctx, approval)
            return await ctx.send('The owner of the sheet could not be found. Deleting sheet from database...')
        # Approve
        if ctx.author.id in approval.approvals:
            return await ctx.send('You have already approved this sheet! You cannot approve it again.')
        approval.approvals.append(ctx.author.id)
        if len(approval.approvals) >= 2:
            await self.approve_sheet(ctx, approval)
            return await ctx.send(f'Sheet has been fully approved! '
                                  f'Contact the Sheet Owner ({sheet_owner.mention}) with approval details.')
        else:
            await self.add_approval(ctx, approval)
            await self.bot.mdb['to_approve'].update_one({'id': approval.id}, {'$set': approval.to_dict()})
            return await ctx.send('You have added your approval to the sheet!')


def setup(bot):
    bot.add_cog(SheetApproval(bot))
