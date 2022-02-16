import discord
import web
import dotenv
import redis
import os
import datetime
import time
import random
import string

client = discord.Bot(intents=discord.Intents().all())
r = redis.Redis(host=os.environ['REDISHOST'], port=int(os.environ['REDISPORT']), username=os.environ['REDISUSER'], password=os.environ['REDISPASSWORD'], db=0)

try:
    dotenv.load_dotenv()
except:
    pass

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}#{client.user.discriminator} ({client.user.id})')

@client.slash_command(description="메신저를 연 특정 플레이어에게 메시지를 보냅니다.", guild_ids=[931316314604179477], permissions=[discord.commands.CommandPermission(931316315011055651, 1, True), discord.commands.CommandPermission(931316315011055650, 1, True), discord.commands.CommandPermission(931316315011055648, 1, True)])
async def 메시지전송(ctx, id):
    if r.get(f'messages_{id}') == None:
        await ctx.respond(':x: 해당 유저의 복구 메신저를 찾을 수 없습니다.', ephemeral=True)
    class MessengerModal(discord.ui.Modal):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            month = datetime.datetime.now().month
            day = datetime.datetime.now().day + 1
            self.add_item(
                discord.ui.InputText(
                    label='전송할 메시지',
                    placeholder=f'{month}월 {day}일 오후 1시에 게임에 접속해주세요.',
                    max_length=500
                )
            )
        async def callback(self, interaction: discord.Interaction):
            message = interaction.data['components'][0]['components'][0]['value']
            message = f'\n\n🛡️ {ctx.author.name} ({ctx.author.id}): {message} - {time.ctime()}'
            messages = r.get(f'messages_{id}').decode('utf-8') + message
            r.set(f'messages_{id}', messages)
            fileName = 'messages_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12)) + '.txt'
            with open(fileName, 'w', encoding='UTF-8') as f: f.write(messages)
            await interaction.response.send_message(':white_check_mark: 전송 완료!', file=discord.File(fileName), ephemeral=True)
            os.remove(fileName)
    await ctx.response.send_modal(MessengerModal(title='복구 메신저'))

@client.slash_command(description="메신저를 연 특정 플레이어와 주고 받은 메시지를 확인합니다.", guild_ids=[931316314604179477], permissions=[discord.commands.CommandPermission(931316315011055651, 1, True), discord.commands.CommandPermission(931316315011055650, 1, True), discord.commands.CommandPermission(931316315011055648, 1, True)])
async def 메시지로그(ctx, id):
    if r.get(f'messages_{id}') == None:
        await ctx.respond(':x: 해당 유저의 복구 메신저를 찾을 수 없습니다.', ephemeral=True)
    fileName = 'messages_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12)) + '.txt'
    with open(fileName, 'w', encoding='UTF-8') as f: f.write(r.get(f'messages_{id}').decode('utf-8'))
    await ctx.respond('📜 메시지 전송 로그', file=discord.File(fileName), ephemeral=True)
    os.remove(fileName)

if __name__ == '__main__':
    web.run()
    client.run(os.environ['TOKEN'])