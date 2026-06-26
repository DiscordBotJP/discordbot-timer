import discord
from discord.ext import commands
from daug.utils.dpyexcept import excepter
import asyncio
import re
import time
from utils.dashboard_config import DashboardConfigCache
from utils.ops_log import emit_message_command_error

seconds_pattern = re.compile(r'\d+秒')
minutes_pattern = re.compile(r'\d+分')
seconds_countdown_pattern = re.compile(r'\d+秒(!|！)')
minutes_countdown_pattern = re.compile(r'\d+分(!|！)')


class TimerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dashboard_config = DashboardConfigCache()
        self.last_response_at_by_guild: dict[int, float] = {}

    @commands.Cog.listener()
    @excepter
    async def on_message(self, message: discord.Message):
        try:
            await self._handle_timer_message(message)
        except Exception as error:
            await emit_message_command_error(message, error)
            raise

    async def _handle_timer_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not any(
            pattern.fullmatch(message.content)
            for pattern in (
                seconds_pattern,
                minutes_pattern,
                seconds_countdown_pattern,
                minutes_countdown_pattern,
            )
        ):
            return
        is_countdown = bool(
            seconds_countdown_pattern.fullmatch(message.content)
            or minutes_countdown_pattern.fullmatch(message.content)
        )
        dashboard_setting = None
        if message.guild is not None:
            settings = await self.dashboard_config.get()
            dashboard_setting = settings.for_guild(message.guild.id)
            if not dashboard_setting.enabled:
                return
            if is_countdown and not dashboard_setting.countdown_enabled:
                await message.reply('カウントダウン通知はこのサーバーでは無効です', delete_after=10)
                return
            last_response_at = self.last_response_at_by_guild.get(message.guild.id, 0)
            interval_seconds = dashboard_setting.interval_minutes * 60
            if interval_seconds > 0 and time.monotonic() - last_response_at < interval_seconds:
                return
            self.last_response_at_by_guild[message.guild.id] = time.monotonic()

        max_timer_seconds = dashboard_setting.max_timer_seconds if dashboard_setting else 600

        if seconds_pattern.fullmatch(message.content):
            seconds = int(message.content.split('秒')[0])
            if seconds > max_timer_seconds:
                await message.reply(f'{max_timer_seconds}秒以内の計測が可能です', delete_after=10)
                return
            await message.reply(f'{seconds}秒測ります（計測終了:<t:{int(time.time()) + seconds + 1}:R>）')
            await asyncio.sleep(seconds)
            await message.channel.send(f'{seconds}秒が経過しました {message.author.mention}')
        if minutes_pattern.fullmatch(message.content):
            minutes = int(message.content.split('分')[0])
            if minutes * 60 > max_timer_seconds:
                await message.reply(f'{max_timer_seconds}秒以内の計測が可能です', delete_after=10)
                return
            await message.reply(f'{minutes}分測ります（計測終了:<t:{int(time.time()) + 60 * minutes + 1}:R>）')
            await asyncio.sleep(minutes * 60)
            await message.channel.send(f'{minutes}分が経過しました {message.author.mention}')
        if seconds_countdown_pattern.fullmatch(message.content):
            seconds = int(message.content.split('秒')[0])
            time_str = f'{seconds}秒'
            if seconds > max_timer_seconds:
                await message.reply(f'{max_timer_seconds}秒以内の計測が可能です', delete_after=10)
                return
            await message.reply(f'{time_str}測ります')
            if seconds > 30:
                await asyncio.sleep(seconds - 30)
                seconds = 30
                await message.channel.send(f'残り30秒です {message.author.mention}')
            if seconds > 10:
                await asyncio.sleep(seconds - 10)
                seconds = 10
                await message.channel.send(f'残り10秒です {message.author.mention}')
            await asyncio.sleep(seconds)
            await message.channel.send(f'{time_str}が経過しました {message.author.mention}')
        if minutes_countdown_pattern.fullmatch(message.content):
            minutes = int(message.content.split('分')[0])
            if minutes * 60 > max_timer_seconds:
                await message.reply(f'{max_timer_seconds}秒以内の計測が可能です', delete_after=10)
                return
            time_str = f'{minutes}分'
            await message.reply(f'{time_str}測ります')
            while minutes > 1:
                await asyncio.sleep(60)
                minutes -= 1
                await message.channel.send(f'残り{minutes}分です {message.author.mention}')
            await asyncio.sleep(30)
            await message.channel.send(f'残り30秒です {message.author.mention}')
            await asyncio.sleep(20)
            await message.channel.send(f'残り10秒です {message.author.mention}')
            await asyncio.sleep(10)
            await message.channel.send(f'{time_str}が経過しました {message.author.mention}')


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TimerCog(bot))
