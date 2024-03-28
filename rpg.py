import discord
from discord.ext import commands
import mysql.connector
import os
import json
import asyncio
from datetime import datetime, timedelta
import random

# MySQL 연결 설정
mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="anthony.k12345.k!",
    database="rpg_db"
)

# MySQL 커서 생성
mycursor = mydb.cursor()

intents = discord.Intents.all()
intents.messages = True
intents.guilds = True  # 서버 정보에 대한 접근 권한 활성화
intents.members = True  # 멤버 목록에 대한 접근 권한 활성화
bot = commands.Bot(command_prefix='!', intents=intents)

# 순위 명령어
@bot.command()
async def 순위(ctx):

    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
    
    # 상위 5명의 user_power 순위를 가져옵니다.
    mycursor.execute("SELECT discord_id, user_power FROM user_rpg ORDER BY user_power DESC LIMIT 5")
    top_users = mycursor.fetchall()

    # 순위 메시지 생성
    rank_message = "**Power 순위**\n"
    rank = 1
    for user in top_users:
        discord_id = user[0]
        user_power = user[1]
        user_info = await bot.fetch_user(int(discord_id))
        rank_message += f"{rank}. {user_info.name} - Power: {user_power}\n"
        rank += 1

    await ctx.send(rank_message)

@bot.command()
async def 출석체크(ctx):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
    
    # 현재 시간 (KST: 한국 표준시)을 가져옵니다.
    now = datetime.utcnow() + timedelta(hours=9)

    # 사용자 정보 가져오기
    discord_id = str(ctx.author.id)
    
    # 해당 Discord ID로 사용자 정보 조회
    mycursor.execute("SELECT user_attendance, user_coin, user_date FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_info = mycursor.fetchone()

    if user_info:
        attendance_status = user_info[0]
        user_coin = user_info[1]
        last_attendance_date = user_info[2]

        # 출석체크 날짜 확인
        if last_attendance_date != now.strftime('%m월%d일') or attendance_status == 'x':
            # 출석체크 처리
            sql_update = "UPDATE user_rpg SET user_attendance = 'o', user_coin = user_coin + 1000, user_date = %s WHERE discord_id = %s"
            val_update = (now.strftime('%m월%d일'), discord_id)
            mycursor.execute(sql_update, val_update)
            mydb.commit()

            # 랜덤스킬팩 아이템 추가
            item_name = '랜덤스킬팩'
            item_amount = 1
            user_inventory_path = f"{discord_id}_inventory.json"
            try:
                with open(user_inventory_path, "r") as file:
                    inventory = json.load(file)
            except FileNotFoundError:
                inventory = []

            inventory.append({'name': item_name, 'quantity': item_amount})

            with open(user_inventory_path, "w") as file:
                json.dump(inventory, file)

            await ctx.send(f'{ctx.author.mention} 님, 출석체크가 완료되었습니다. 1,000 coin이 지급되었으며 랜덤스킬팩을 획득하셨습니다.')
        else:
            await ctx.send(f'{ctx.author.mention} 님은 이미 출석체크를 하셨습니다.')
    else:
        await ctx.send(f'{ctx.author.mention} 님의 정보를 찾을 수 없습니다.')

@bot.command()
async def 회원가입(ctx):

    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return

    # 유저 정보 가져오기
    discord_id = str(ctx.author.id)
    discord_name = str(ctx.author)

    # 해당 Discord ID가 이미 존재하는지 확인
    mycursor.execute("SELECT * FROM user_rpg WHERE discord_id = %s", (discord_id,))
    existing_user = mycursor.fetchone()

    if existing_user:
        await ctx.send(f'{ctx.author.mention} 님은 이미 회원가입되어 있습니다!')
    else:
        # 데이터베이스에 저장
        sql = "INSERT INTO user_rpg (discord_id, discord_name, user_login, user_character) VALUES (%s, %s, 'x', 'x')"
        val = (discord_id, discord_name)
        mycursor.execute(sql, val)
        mydb.commit()

        await ctx.send(f'{ctx.author.mention} 님의 회원가입이 완료되었습니다!')

@bot.command()
async def 로그인(ctx):

    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return

    # 유저 정보 가져오기
    discord_id = str(ctx.author.id)
    
    # 해당 Discord ID로 사용자 정보 조회
    mycursor.execute("SELECT user_login FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_login_status = mycursor.fetchone()

    if user_login_status:
        if user_login_status[0] == 'x':
            # 로그인 처리
            sql = "UPDATE user_rpg SET user_login = 'o' WHERE discord_id = %s"
            val = (discord_id,)
            mycursor.execute(sql, val)
            mydb.commit()

            await ctx.send(f'{ctx.author.mention} 님, 로그인에 성공했습니다!')
        else:
            await ctx.send(f'{ctx.author.mention} 님은 이미 로그인되어 있습니다!')
    else:
        await ctx.send(f'{ctx.author.mention} 님은 회원가입되어 있지 않습니다. 먼저 회원가입을 진행해주세요.')

@bot.command()
async def 로그아웃(ctx):

    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return

    # 유저 정보 가져오기
    discord_id = str(ctx.author.id)
    
    # 해당 Discord ID로 사용자 정보 조회
    mycursor.execute("SELECT user_login FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_login_status = mycursor.fetchone()

    if user_login_status:
        if user_login_status[0] == 'o':
            # 로그아웃 처리
            sql = "UPDATE user_rpg SET user_login = 'x' WHERE discord_id = %s"
            val = (discord_id,)
            mycursor.execute(sql, val)
            mydb.commit()

            await ctx.send(f'{ctx.author.mention} 님, 로그아웃되었습니다!')
        else:
            await ctx.send(f'{ctx.author.mention} 님은 이미 로그아웃되어 있습니다!')
    else:
        await ctx.send(f'{ctx.author.mention} 님은 회원가입되어 있지 않습니다. 먼저 회원가입을 진행해주세요.')

@bot.command()
async def 서버선택(ctx, sever: int):  # sever 매개변수 추가

    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return

    if sever < 1 or sever > 4:
        await ctx.send("잘못된 서버 번호입니다. 1에서 4까지의 번호 중 하나를 선택해주세요.")
        return
    
    discord_id = str(ctx.author.id)
    mycursor.execute("SELECT user_sever FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_sever = mycursor.fetchone()[0]

    if user_sever is not None:
        await ctx.send(f'{ctx.author.mention} 님은 이미 서버를 선택하셨습니다!')
    else:
        mycursor.execute("UPDATE user_rpg SET user_sever = %s WHERE discord_id = %s", (sever, discord_id))
        mydb.commit()
        await ctx.send(f'{ctx.author.mention} 님, 서버 선택이 완료되었습니다!')

@bot.command()
async def 캐릭터생성(ctx):

    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return

    discord_id = str(ctx.author.id)

    mycursor.execute("SELECT user_character, user_sever FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_info = mycursor.fetchone()

    if user_info:
        user_character_status = user_info[0]
        user_sever = user_info[1]

        if user_character_status == 'x' and user_sever is not None:
            sql = "UPDATE user_rpg SET user_character = 'o', user_exp = 0 WHERE discord_id = %s"
            val = (discord_id,)
            mycursor.execute(sql, val)

            # 처음 캐릭터 생성 시 추가 정보 초기값 설정
            sql_init_info = "UPDATE user_rpg SET user_level = 1, user_power = 1000, user_location = '시작 마을', user_coin = 5000 WHERE discord_id = %s"
            mycursor.execute(sql_init_info, (discord_id,))

            # 인벤토리를 저장하는 JSON 파일 생성
            inventory_file_path = f"{discord_id}.json"
            if not os.path.exists(inventory_file_path):
                with open(inventory_file_path, "w") as file:
                    json.dump([], file)

            mydb.commit()

            await ctx.send(f'{ctx.author.mention} 님의 캐릭터가 생성되었습니다!')
        elif user_character_status == 'o':
            await ctx.send(f'{ctx.author.mention} 님은 이미 캐릭터를 생성하셨습니다!')
        else:
            await ctx.send(f'{ctx.author.mention} 님은 서버를 선택하지 않았습니다. 먼저 서버를 선택해주세요.')
    else:
        await ctx.send(f'{ctx.author.mention} 님은 회원가입되어 있지 않습니다. 먼저 회원가입을 진행해주세요.')
 
@bot.command() 
async def 전직(ctx, *, user_class: str):
 
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
 
    class_files = {
        "버서커": ("C:\\Users\\kwon1\\class\\berserker.png", "C:/Users/kwon1/berserker.txt"),
        "가디언": ("C:\\Users\\kwon1\\class\\knight.png", "C:/Users/kwon1/knight.txt"),
        "레인저": ("C:\\Users\\kwon1\\class\\ranger.jpg", "C:/Users/kwon1/ranger.txt"),
        "데몬 헌터": ("C:\\Users\\kwon1\\class\\demon hunter.png", "C:/Users/kwon1/demon hunter.txt"),
        "어쌔신": ("C:\\Users\\kwon1\\class\\assassin.png", "C:/Users/kwon1/assassin.txt"),
        "몽크": ("C:\\Users\\kwon1\\class\\monk.png", "C:/Users/kwon1/monk.txt"),
        "배틀 메이지": ("C:\\Users\\kwon1\\class\\battle mage.png", "C:/Users/kwon1/battle mage.txt"),
        "네크로맨서": ("C:\\Users\\kwon1\\class\\necromancer.png", "C:/Users/kwon1/necromancer.txt")
    }
 
    # 입력된 클래스명이 허용된 클래스인지 확인
    if user_class not in class_files:
        await ctx.send("유효하지 않은 클래스입니다. 다음 중 하나를 선택해주세요: " + ", ".join(class_files.keys()))
        return
 
    discord_id = str(ctx.author.id)
    mycursor.execute("SELECT user_character FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_character = mycursor.fetchone()
 
    # 캐릭터가 생성되지 않은 경우
    if user_character is None or user_character[0] != 'o':
        await ctx.send(f"{ctx.author.mention} 님, 먼저 캐릭터를 생성해주세요!")
        return
 
    mycursor.execute("SELECT user_class FROM user_rpg WHERE discord_id = %s", (discord_id,))
    current_class = mycursor.fetchone()
 
    # 이미 선택한 클래스인 경우
    if current_class and current_class[0] is not None:
        await ctx.send(f'{ctx.author.mention} 님은 이미 {current_class[0]} 클래스를 선택하셨습니다!')
    else:
        selected_class = user_class
        profile_picture_path, class_file_path = class_files[selected_class]
        
        # 파일에서 클래스 정보 읽어오기 (UTF-8 인코딩 사용)
        with open(class_file_path, 'r', encoding='utf-8') as file:
            class_info = file.readlines()
 
        # 정보 추출
        user_type = None
        stats_atk, stats_def, stats_hp, stats_mhp, stats_mp, stats_mmp = None, None, None, None, None, None
        
        for line in class_info:
            key, value = line.split('=')
            key = key.strip()
            value = value.strip()
            if key == 'type':
                user_type = value
            elif key == 'atk':
                stats_atk = int(value)  # 공격력
            elif key == 'def':
                stats_def = int(value)  # 방어력
            elif key == 'hp':
                stats_hp, stats_mhp = map(int, value.split('/'))  # 체력
            elif key == 'mp':
                stats_mp, stats_mmp = map(int, value.split('/'))  # 마나
 
        # 전투력 계산
        user_power = (stats_atk * 1500) + (stats_def * 1500) + (stats_hp * 500) + (stats_mp * 2000)
 
        # 데이터베이스 업데이트
        mycursor.execute("UPDATE user_rpg SET user_class = %s, user_type = %s, stats_atk = %s, stats_def = %s, stats_hp = %s, stats_Mhp = %s, stats_mp = %s, stats_Mmp = %s, user_power = %s WHERE discord_id = %s", 
                         (selected_class, user_type, stats_atk, stats_def, stats_hp, stats_mhp, stats_mp, stats_mmp, user_power, discord_id))
        mydb.commit()
 
        # 프로필 사진과 함께 임베드 메시지 보내기
        embed = discord.Embed(title="전직 완료", description=f"{ctx.author.mention} 님, {selected_class} 클래스를 선택하셨습니다!", color=0x00ff00)
        embed.add_field(name="타입", value=user_type, inline=False)
        embed.add_field(name="전투력", value=user_power, inline=False)  # 전투력 표시
        embed.add_field(name="공격력", value=stats_atk, inline=False)
        embed.add_field(name="방어력", value=stats_def, inline=False)
        embed.add_field(name="체력", value=f"{stats_hp} / {stats_mhp}", inline=False)
        embed.add_field(name="마나", value=f"{stats_mp} / {stats_mmp}", inline=False)
        embed.set_thumbnail(url="attachment://" + profile_picture_path.split("\\")[-1])
        await ctx.send(embed=embed, file=discord.File(profile_picture_path))
        
@bot.command()
async def 인벤(ctx):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return

    discord_id = str(ctx.author.id)
    inventory_file_path = f"{discord_id}_inventory.json"

    try:
        with open(inventory_file_path, "r") as file:
            inventory = json.load(file)
    except FileNotFoundError:
        inventory = []

    if not inventory:
        await ctx.send("인벤토리가 비어 있습니다.")
    else:
        # 중복된 아이템 병합
        unique_items = {}
        for item in inventory:
            name = item['name']
            quantity = item['quantity']
            if name in unique_items:
                unique_items[name] += quantity
            else:
                unique_items[name] = quantity
        
        inventory_list = "\n".join([f"{name} ({quantity}개)" for name, quantity in unique_items.items()])
        await ctx.send(f"{ctx.author.mention} 님의 인벤토리:\n{inventory_list}")

# 전역 범위에서 이동 중인 플레이어를 추적하는 세트
moving_players = set()

# 위치 ID와 위치 이름을 매핑하는 딕셔너리
location_names = {
    1: "시작 마을",
    2: "실버폴 스트리트",
    3: "올드움 대성당",
    4: "용의 눈 호수",
    5: "황혼의 숲",
    6: "섀도우키퍼 요새",
    7: "비명의 협곡",
    8: "마법학교 아르카네움",
    9: "황금해안 마을",
    10: "대지의 심장 동굴",
    11: "불꽃의 늪"
}

@bot.command()
async def 이동(ctx, location_id: int):
    global moving_players

    if ctx.author.id in moving_players:
        await ctx.send("이미 이동 중입니다.")
        return

    discord_id = str(ctx.author.id)

    # 사용자의 레벨을 가져옵니다.
    mycursor.execute("SELECT user_level FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_level_result = mycursor.fetchone()
    if user_level_result:
        user_level = user_level_result[0]
    else:
        await ctx.send("사용자의 레벨 정보를 가져올 수 없습니다.")
        return

    # 사용자의 현재 위치를 가져옵니다.
    mycursor.execute("SELECT user_location FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_location_name = mycursor.fetchone()[0]

    # 이동할 위치와 현재 위치가 같은 경우 처리
    if location_names[location_id] == user_location_name:
        await ctx.send("이미 해당 위치에 있습니다.")
        return

    # 장소별 레벨 제한 설정
    location_level_limits = {
        1: 1,
        2: 1,
        3: 10,
        4: 20,
        5: 30,
        6: 40,
        7: 50,
        8: 60,
        9: 70,
        10: 80,
        11: 90
    }

    # 입력된 위치 ID가 유효한지 확인
    if location_id < 1 or location_id > 11:
        await ctx.send("유효하지 않은 위치 ID입니다.")
        return

    # 사용자의 레벨이 해당 장소의 레벨 제한보다 큰지 확인
    location_level_limit = location_level_limits.get(location_id)
    if location_level_limit is None:
        await ctx.send("해당 장소에는 레벨 제한이 설정되어 있지 않습니다.")
        return

    if user_level < location_level_limit:
        await ctx.send(f"해당 장소로 이동하기에는 레벨이 부족합니다. {location_level_limit} 레벨 이상이어야 합니다.")
        return

    # 이동 시작 메시지 전송
    move_message = await ctx.send(f"{ctx.author.mention} 님이 {location_names[location_id]}로 이동중입니다. 이동 완료까지 30초가 소요됩니다.")

    # 이동 중인 플레이어 목록에 추가
    moving_players.add(ctx.author.id)

    # 이동 완료까지 30초 대기
    await asyncio.sleep(30)

    # 유저의 위치를 해당 장소로 업데이트
    mycursor.execute("UPDATE user_rpg SET user_location = %s WHERE discord_id = %s", (location_names[location_id], discord_id))
    mydb.commit()

    # 이동 완료 메시지 전송
    await move_message.edit(content=f"{ctx.author.mention} 님이 {location_names[location_id]}로 이동하셨습니다!")

    # 이동 완료 후 이동 중인 플레이어 목록에서 제거
    moving_players.remove(ctx.author.id)

# 몬스터 정보 정의
MONSTERS = {
    "슬라임": {
        'atk': 5,
        'def': 12,
        'hp': 50,
        'mp': 0,
        'coin': 10,  # 슬라임이 드랍하는 코인의 양
        'exp': 1000,  # 슬라임이 드랍하는 경험치의 양
        'drops': [
            {'item': '슬라임 점액', 'amount': 1, 'drop_rate': 0.3},
            {'item': '슬라임 조각', 'amount': 2, 'drop_rate': 1}
        ]
    },
    "고블린": {
        'atk': 15,
        'def': 8,
        'hp': 25,
        'mp': 0,
        'coin': 20,  # 고블린이 드랍하는 코인의 양
        'exp': 30,  # 고블린이 드랍하는 경험치의 양
        'drops': [
            {'item': '고블린 귀걸이', 'amount': 1, 'drop_rate': 0.2}
        ]
    }
}

# 몬스터 정보와 위치 정보를 매핑하는 딕셔너리
MONSTER_LOCATIONS = {
    "슬라임": ["실버폴 스트리트"],
    "고블린": ["실버폴 스트리트"],
}

# 몬스터 정보를 가져오는 함수
def get_monster_info_by_name(monster_name):
    return MONSTERS.get(monster_name)

# 사용자 정보를 가져오는 함수
def get_user_info(user_id):
    mycursor = mydb.cursor()
    mycursor.execute("SELECT stats_atk, stats_def, stats_hp, stats_mp, stats_point, user_level, user_exp, stats_mhp, stats_mmp FROM user_rpg WHERE discord_id = %s", (user_id,))
    user_info = mycursor.fetchone()
    mycursor.close()
    return user_info

# 스탯 포인트를 포함하여 사용자 정보를 업데이트하는 함수
def update_user_info(user_id, stats):
    mycursor = mydb.cursor()
    
    # 'mhp' 및 'mmp' 키가 stats 사전에 이미 존재하는지 확인합니다.
    if 'mhp' not in stats:
        mycursor.execute("SELECT stats_mhp FROM user_rpg WHERE discord_id = %s", (user_id,))
        mhp = mycursor.fetchone()[0]
        stats['mhp'] = mhp  # 'mhp' 키가 없는 경우 기존 값으로 설정합니다.
    if 'mmp' not in stats:
        mycursor.execute("SELECT stats_mmp FROM user_rpg WHERE discord_id = %s", (user_id,))
        mmp = mycursor.fetchone()[0]
        stats['mmp'] = mmp  # 'mmp' 키가 없는 경우 기존 값으로 설정합니다.
    
    mycursor.execute("UPDATE user_rpg SET stats_atk = %s, stats_def = %s, stats_hp = %s, stats_mp = %s, stats_point = %s, stats_mhp = %s, stats_mmp = %s WHERE discord_id = %s", (stats['atk'], stats['def'], stats['hp'], stats['mp'], stats['stats_point'], stats['mhp'], stats['mmp'], user_id))
    mydb.commit()
    mycursor.close()

def calculate_required_exp(user_level):
    if user_level < 10:
        return 1000
    elif user_level < 20:
        return 5000
    elif user_level < 30:
        return 25000
    elif user_level < 40:
        return 50000
    elif user_level < 50:
        return 100000
    elif user_level < 60:
        return 150000
    elif user_level < 70:
        return 300000
    elif user_level < 80:
        return 500000
    elif user_level < 90:
        return 1000000
    elif user_level < 100:
        return 2500000
    else:
        return 5000000

# 몬스터 스탯을 추출하는 함수
def extract_monster_stats(monster_info):
    return {
        'atk': monster_info['atk'],
        'def': monster_info['def'],
        'hp': monster_info['hp'],
        'mp': monster_info['mp']
    }

# 스탯 정보를 포맷팅하여 문자열로 반환하는 함수
def format_stats(stats):
    return f"공격력: {stats['atk']}, 방어력: {stats['def']}, 체력: {stats['hp']}, 마나: {stats['mp']}"

def combat(user_stats, monster_stats):
    user_hp = user_stats['hp']
    monster_hp = monster_stats['hp']
    user_defense = user_stats['def']
    monster_defense = monster_stats['def']
    
    # 사용자의 공격
    user_damage = max(1, int(user_stats['atk'] - (monster_defense / (monster_defense + 10))))
    monster_hp -= user_damage
    
    # 몬스터의 공격
    monster_damage = max(1, int(monster_stats['atk'] - (user_defense / (user_defense + 10))))
    user_hp -= monster_damage
    
    # 최종 체력을 갱신
    user_stats['hp'] = max(0, user_hp)
    monster_stats['hp'] = max(0, monster_hp)
    
    # 전투 결과와 데미지 반환
    if user_hp > 0 and monster_hp <= 0:
        return "user_win", user_damage, monster_damage
    elif user_hp <= 0 and monster_hp > 0:
        return "monster_win", user_damage, monster_damage
    else:
        return "draw", user_damage, monster_damage

@bot.command()
async def 사냥(ctx, *, monster_name: str):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
    
    # 몬스터 정보 가져오기
    monster_info = MONSTERS.get(monster_name)

    if not monster_info:
        await ctx.send("해당하는 몬스터를 찾을 수 없습니다.")
        return

    # 사용자의 현재 위치 가져오기
    discord_id = str(ctx.author.id)
    mycursor.execute("SELECT user_location FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_location = mycursor.fetchone()

    if not user_location:
        await ctx.send("사용자의 위치를 가져올 수 없습니다.")
        return

    # 사용자의 위치가 몬스터의 출현 가능한 위치에 있는지 확인
    monster_spawn_locations = MONSTER_LOCATIONS.get(monster_name)
    if user_location[0] not in monster_spawn_locations:
        await ctx.send("현재 위치에서는 이 몬스터를 찾을 수 없습니다.")
        return

    # 전투 시작 전에 사용자 정보를 실시간으로 가져옴
    user_info = get_user_info(ctx.author.id)

    if not user_info:
        await ctx.send("사용자 정보를 찾을 수 없습니다.")
        return

    user_stats = {
        'atk': user_info[0],
        'def': user_info[1],
        'hp': user_info[2],
        'mp': user_info[3],
        'stats_point': user_info[4],  # 스탯 포인트 정보 추가
        'level': user_info[5],
        'exp': user_info[6],
        'mhp': user_info[7],
        'mmp': user_info[8]
    }
    monster_stats = extract_monster_stats(monster_info)

    # 사용자 스탯 표시
    user_stat_string = format_stats(user_stats)
    monster_stat_string = format_stats(monster_stats)
    
    embed = discord.Embed(title="전투 시작", color=0xff0000)
    embed.add_field(name=f"{ctx.author.display_name} 스탯", value=user_stat_string, inline=True)
    embed.add_field(name=f"{monster_name} 스탯", value=monster_stat_string, inline=True)
    embed.set_footer(text="⚔️를 눌러 공격하세요.")

    message = await ctx.send(embed=embed)

    await message.add_reaction("⚔️")  # 이모지 추가

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == "⚔️" and reaction.message.id == message.id

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check)  # 여기서 대기
    except asyncio.TimeoutError:
        await ctx.send("시간이 초과되었습니다. 전투를 종료합니다.")
        return

    turn_count = 0

    # 한 번의 이모지 반응으로 한 턴만 진행되도록 변경
    while user_stats['hp'] > 0 and monster_stats['hp'] > 0:
        turn_count += 1

        # 사용자가 몬스터를 공격
        result, user_damage, monster_damage = combat(user_stats, monster_stats)

        # 전투 진행 메시지 작성
        result_message = (
            f"**[{turn_count}턴]**\n"
            f"{ctx.author.display_name}이/가 {monster_name}를 공격했습니다.\n"
            f"{monster_name}에게 {user_damage}의 피해를 입혔습니다.\n"
            f"남은 체력 - {ctx.author.display_name}: {user_stats['hp']}, {monster_name}: {monster_stats['hp']}\n"
        )

        # 메시지 업데이트
        embed.description = result_message
        await message.edit(embed=embed)

        try:
            reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check)  # 여기서 대기
        except asyncio.TimeoutError:
            await ctx.send("시간이 초과되었습니다. 전투를 종료합니다.")
            return

        if user_stats['hp'] <= 0 or monster_stats['hp'] <= 0:
            break

        # 몬스터가 사용자를 공격
        result, user_damage, monster_damage = combat(user_stats, monster_stats)

        # 전투 진행 메시지 작성
        result_message = (
            f"**[{turn_count}턴]**\n"
            f"{monster_name}이/가 {ctx.author.display_name}를 공격했습니다.\n"
            f"{ctx.author.display_name}에게 {monster_damage}의 피해를 입혔습니다.\n"
            f"남은 체력 - {ctx.author.display_name}: {user_stats['hp']}, {monster_name}: {monster_stats['hp']}\n"
        )

        # 메시지 업데이트
        embed.description = result_message
        await message.edit(embed=embed)

        if user_stats['hp'] <= 0 or monster_stats['hp'] <= 0:
            break

    # 전투 결과 확인
    if user_stats['hp'] <= 0:
        await ctx.send("전투가 종료되었습니다. 몬스터에게 패배하였습니다.")
    elif monster_stats['hp'] <= 0:
        # 몬스터가 죽었을 경우 사용자의 코인과 경험치를 증가시킴
        coin_drop = monster_info.get('coin', 0)
        exp_drop = monster_info.get('exp', 0)
        await ctx.send(f"전투가 종료되었습니다. 몬스터를 격파하였습니다.\n 획득한 코인: {coin_drop}, 획득한 경험치: {exp_drop}")
        # 사용자의 코인과 경험치 업데이트
        mycursor.execute("UPDATE user_rpg SET user_coin = user_coin + %s, user_exp = user_exp + %s WHERE discord_id = %s", (coin_drop, exp_drop, ctx.author.id))
        # 레벨 업데이트 확인
        user_level = user_stats['level']
        required_exp = calculate_required_exp(user_level)
        while user_stats['exp'] >= required_exp:
            user_stats['level'] += 1
            user_stats['exp'] -= required_exp
            user_stats['stats_point'] += 3  # 레벨업 시 스탯 포인트 추가
            # 레벨업 시 체력과 마나를 최대치로 회복
            user_stats['hp'] = user_stats['mhp'] # max_hp는 사용자의 최대 체력을 저장하는 변수입니다.
            user_stats['mp'] = user_stats['mmp'] # max_mp는 사용자의 최대 마나를 저장하는 변수입니다.
            await ctx.send(f"레벨 업! {ctx.author.display_name}님은 레벨 {user_stats['level']}이 되었습니다! 스탯 포인트 3개를 획득하셨습니다.")
            mycursor.execute("UPDATE user_rpg SET user_level = %s, user_exp = %s, stats_point = %s, stats_hp = %s, stats_mp = %s, stats_mhp = %s, stats_mmp = %s WHERE discord_id = %s", (user_stats['level'], user_stats['exp'], user_stats['stats_point'], user_stats['hp'], user_stats['mp'], user_stats['mhp'], user_stats['mmp'], ctx.author.id))
        mydb.commit()
    else:
        await ctx.send("전투가 종료되었습니다. 전투가 계속 중입니다.")

    # 아이템 드롭 여부 확인
    for drop in monster_info.get('drops', []):
        if random.random() < drop['drop_rate']:
            item_name = drop['item']
            item_amount = drop['amount']
            await ctx.send(f"{monster_name}이(가) {item_name}을(를) {item_amount}개 드롭하였습니다.")
            # 아이템을 인벤토리에 추가
            discord_id = str(ctx.author.id)
            inventory_file_path = f"{discord_id}_inventory.json"

            try:
                with open(inventory_file_path, "r") as file:
                    inventory = json.load(file)
            except FileNotFoundError:
                inventory = []

            # 인벤토리에 아이템 추가
            item_exists = False
            for item in inventory:
                if item['name'] == item_name:
                    item['quantity'] += item_amount
                    item_exists = True
                    break
        
            if not item_exists:
                inventory.append({'name': item_name, 'quantity': item_amount})

            # 인벤토리를 JSON 파일에 저장
            with open(inventory_file_path, "w") as file:
                json.dump(inventory, file)

    # 전투 종료 후 사용자 정보 업데이트
    update_user_info(ctx.author.id, user_stats)

@bot.command()
async def 스탯업(ctx, stat_name: str, amount: int):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
    # 사용자 정보 가져오기
    user_info = get_user_info(ctx.author.id)

    if not user_info:
        await ctx.send("사용자 정보를 찾을 수 없습니다.")
        return

    user_stats = {
        'atk': user_info[0],
        'def': user_info[1],
        'hp': user_info[2],
        'mp': user_info[3],
        'stats_point': user_info[4],  # 스탯 포인트 정보 추가
        'level': user_info[5],
        'exp': user_info[6]
    }

    # 스탯 포인트가 충분한지 확인
    if user_stats['stats_point'] < amount:
        await ctx.send("스탯 포인트가 부족합니다.")
        return

    # 스탯을 올릴 수 있는지 확인하고 올리기
    if stat_name == "공격력":
        user_stats['atk'] += amount
    elif stat_name == "방어력":
        user_stats['def'] += amount
    elif stat_name == "최대체력":
        user_stats['hp'] += amount
    elif stat_name == "최대마나":
        user_stats['mp'] += amount
    else:
        await ctx.send("잘못된 스탯 이름입니다.")
        return

    # 스탯 포인트 차감
    user_stats['stats_point'] -= amount

    # 사용자 정보 업데이트
    update_user_info(ctx.author.id, user_stats)

    await ctx.send(f"{ctx.author.display_name}님의 {stat_name}이/가 {amount}만큼 올라갔습니다.")

@bot.command()
async def 사용(ctx, item_name: str, amount: int):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
    
    discord_id = str(ctx.author.id)
    user_inventory_path = f"{discord_id}_inventory.json"
    
    # 인벤토리 파일 읽기
    try:
        with open(user_inventory_path, "r") as file:
            inventory = json.load(file)
    except FileNotFoundError:
        await ctx.send(f"{ctx.author.mention} 님의 인벤토리가 비어있습니다.")
        return
    
    # 랜덤스킬팩 확인
    for item in inventory:
        if item['name'] == '랜덤스킬팩':
            # 랜덤스킬팩 사용 가능
            if item['quantity'] >= amount:
                # 랜덤스킬팩 사용 후 인벤토리에서 개수 차감
                item['quantity'] -= amount
                if item['quantity'] == 0:
                    inventory.remove(item)
                
                # 스킬 획득
                skills = ['파이어 브레스', '워터 토네이도', '아이스 쉴드']
                obtained_skills = random.sample(skills, amount)
                
                # 획득한 스킬을 파일에 저장
                user_skill_path = f"{discord_id}_skill.json"
                try:
                    with open(user_skill_path, "r") as file:
                        user_skills = json.load(file)
                except FileNotFoundError:
                    user_skills = []

                user_skills.extend(obtained_skills)

                with open(user_skill_path, "w") as file:
                    json.dump(user_skills, file)
                
                # 인벤토리 파일 업데이트
                with open(user_inventory_path, "w") as file:
                    json.dump(inventory, file)
                
                await ctx.send(f"{ctx.author.mention} 님, 랜덤스킬팩 {amount}개를 사용하여 {', '.join(obtained_skills)} 스킬을 획득하였습니다.")
                return
            else:
                await ctx.send(f"{ctx.author.mention} 님의 인벤토리에 랜덤스킬팩이 부족합니다.")
                return
    
    await ctx.send(f"{ctx.author.mention} 님의 인벤토리에 랜덤스킬팩이 없습니다.")

@bot.command()
async def 스킬목록(ctx):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
    
    discord_id = str(ctx.author.id)
    user_skill_path = f"{discord_id}_skill.json"
    
    try:
        with open(user_skill_path, "r") as file:
            user_skills = json.load(file)
        
        if user_skills:
            unique_skills = set(user_skills)  # 중복 제거
            skill_list = "\n".join(unique_skills)
            await ctx.send(f"{ctx.author.mention} 님의 스킬 목록:\n{skill_list}")
        else:
            await ctx.send(f"{ctx.author.mention} 님은 아직 스킬을 획득하지 않았습니다.")
    except FileNotFoundError:
        await ctx.send(f"{ctx.author.mention} 님은 아직 스킬을 획득하지 않았습니다.")

@bot.command()
async def 스킬사용(ctx, skill_name: str):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
    
    discord_id = str(ctx.author.id)
    user_skill_path = f"{discord_id}_skill.json"
    
    try:
        with open(user_skill_path, "r") as file:
            user_skills = json.load(file)
        
        if skill_name not in user_skills:
            # 해당 스킬을 user_skill 데이터베이스에 저장
            mycursor.execute("UPDATE user_rpg SET user_skill = %s WHERE discord_id = %s", (skill_name, discord_id))
            mydb.commit()
            user_skills.append(skill_name)
            with open(user_skill_path, "w") as file:
                json.dump(user_skills, file)
            await ctx.send(f"{ctx.author.mention} 님이 {skill_name} 스킬을 사용했습니다.")
        else:
            await ctx.send(f"{skill_name} 스킬을 이미 보유하고 있습니다.")
    except FileNotFoundError:
        await ctx.send(f"{ctx.author.mention} 님은 아직 스킬을 획득하지 않았습니다.")

@bot.command()
async def 스킬해제(ctx, skill_name: str):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
        
    discord_id = str(ctx.author.id)
    
    # 스킬을 user_skill 데이터베이스에서 해제
    mycursor.execute("UPDATE user_rpg    SET user_skill = NULL WHERE discord_id = %s AND user_skill = %s", (discord_id, skill_name))
    mydb.commit()
    await ctx.send(f"{ctx.author.mention} 님이 {skill_name} 스킬을 해제했습니다.")

@bot.command()
async def 내정보(ctx):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
    discord_id = str(ctx.author.id)
    
    # 사용자 정보 가져오기
    mycursor.execute("SELECT discord_name, user_level, user_exp, user_coin, user_location, user_sever, user_class, stats_atk, stats_def, stats_hp, stats_mhp, stats_mp, stats_mmp, user_power, stats_point FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_info = mycursor.fetchone()
    
    if not user_info:
        await ctx.send("사용자 정보를 찾을 수 없습니다.")
        return
    
    # 레벨업에 필요한 경험치 계산
    user_level = user_info[1]
    user_exp = user_info[2]
    required_exp = calculate_required_exp(user_level)
    exp_to_next_level = required_exp - user_exp
        
    # 스킬 정보 가져오기
    mycursor.execute("SELECT user_skill FROM user_rpg WHERE discord_id = %s", (discord_id,))
    user_skills = mycursor.fetchone()[0]  # user_skill 컬럼의 값 가져오기
    
    # 정보 표시
    embed = discord.Embed(title="내 정보", color=0xff0000)
    if ctx.author.avatar:
        embed.set_thumbnail(url=ctx.author.avatar.url)  # 사용자의 프로필 사진을 썸네일로 설정
    embed.add_field(name="유저 이름", value=user_info[0], inline=True)
    embed.add_field(name="전투력", value=user_info[13], inline=False)
    embed.add_field(name="레벨", value=f"레벨: {user_info[1]}\n경험치: {user_info[2]}/{required_exp}", inline=True)
    embed.add_field(name="서버", value=user_info[5], inline=False)
    embed.add_field(name="위치", value=user_info[4], inline=True)
    embed.add_field(name="코인", value=user_info[3], inline=False)
    
    # 스탯 표시
    embed.add_field(name="스탯", value=f"클래스: {user_info[6]}\n공격력: {user_info[7]}\n방어력: {user_info[8]}\n체력: {user_info[9]}/{user_info[10]}\n마나: {user_info[11]}/{user_info[12]}\n스탯포인트: {user_info[14]}", inline=False)
    
    # 스킬 표시
    embed.add_field(name="스킬", value=user_skills if user_skills else "없음", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def 상점(ctx):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
    try:
        with open(r'C:\Users\kwon1\shop.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()

        item_info = {}
        index = 1

        for line in lines:
            line = line.strip()
            if line.startswith("index:"):
                index = int(line.split(":")[1].strip())
            elif line.startswith("아이템 이름:"):
                item_info[index] = {"이름": line.split(":")[1].strip()}
            elif line.startswith("설명:"):
                item_info[index]["설명"] = line.split(":")[1].strip()
            elif line.startswith("가격:"):
                item_info[index]["가격"] = line.split(":")[1].strip()
            elif line.startswith("이미지:"):
                item_info[index]["이미지"] = line.split(":", 1)[1].strip()

        embed_pages = []
        embed = None
        count = 0
        for index, info in item_info.items():
            if count % 4 == 0:
                if embed is not None:
                    embed_pages.append(embed)
                embed = discord.Embed(title=f"상점 목록 (페이지 {len(embed_pages) + 1})", color=0x00ff00)
            if "이미지" in info:
                embed.set_image(url="attachment://image.jpg")
            embed.add_field(name=f"#{index}: {info['이름']}", value=f"설명: {info['설명']}\n가격: {info['가격']}", inline=False)
            count += 1
        if embed is not None:
            embed_pages.append(embed)

        current_page = 0
        message = await ctx.send(embed=embed_pages[current_page])

        # 이모지 추가
        if len(embed_pages) > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

        while True:
            try:
                reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check)
                if str(reaction.emoji) == "➡️" and current_page < len(embed_pages) - 1:
                    current_page += 1
                    await message.edit(embed=embed_pages[current_page])
                elif str(reaction.emoji) == "⬅️" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=embed_pages[current_page])
                await message.clear_reactions()
                if len(embed_pages) > 1:
                    await message.add_reaction("⬅️")
                    await message.add_reaction("➡️")
                await reaction.remove(ctx.author)
            except TimeoutError:
                break

    except FileNotFoundError:
        await ctx.send("상점 파일을 찾을 수 없습니다.")
    except Exception as e:
        await ctx.send(f"오류가 발생했습니다: {e}")

@bot.command()
async def 구매(ctx, item_index: int, quantity: int = 1):
    if ctx.author.id in moving_players:
        await ctx.send("이동중에는 명령어를 사용할 수 없습니다.")
        return
    discord_id = str(ctx.author.id)
    
    # 상점 파일 읽기
    try:
        with open(r'C:\Users\kwon1\shop.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()

        item_info = {}
        index = 1

        for line in lines:
            line = line.strip()
            if line.startswith("index:"):
                index = int(line.split(":")[1].strip())
            elif line.startswith("아이템 이름:"):
                item_info[index] = {"이름": line.split(":")[1].strip()}
            elif line.startswith("설명:"):
                item_info[index]["설명"] = line.split(":")[1].strip()
            elif line.startswith("가격:"):
                item_info[index]["가격"] = int(line.split(":")[1].strip().replace("coin", ""))
            elif line.startswith("이미지:"):
                item_info[index]["이미지"] = line.split(":", 1)[1].strip()

        # 아이템 구매 처리
        if item_index in item_info:
            item_name = item_info[item_index]["이름"]
            item_price = item_info[item_index]["가격"] * quantity
            # 사용자 정보에서 코인 확인
            mycursor.execute("SELECT user_coin FROM user_rpg WHERE discord_id = %s", (discord_id,))
            user_coin = mycursor.fetchone()[0]
            if user_coin >= item_price:
                # 코인 갱신
                new_coin = user_coin - item_price
                mycursor.execute("UPDATE user_rpg SET user_coin = %s WHERE discord_id = %s", (new_coin, discord_id))
                mydb.commit()
                # 사용자 인벤토리에 아이템 추가
                inventory_path = f"{discord_id}_inventory.json"
                try:
                    with open(inventory_path, "r") as inventory_file:
                        inventory = json.load(inventory_file)
                except FileNotFoundError:
                    inventory = []
                
                for _ in range(quantity):
                    inventory.append({"name": item_name, "quantity": 1})
                
                with open(inventory_path, "w") as inventory_file:
                    json.dump(inventory, inventory_file)
                
                await ctx.send(f"{ctx.author.mention} 님이 {item_name}을(를) {quantity}개 구매했습니다! " + '\n' + 
                               f"사용한 코인: {item_price}coin, 남은 코인: {new_coin}coin")
            else:
                await ctx.send("코인이 부족하여 구매할 수 없습니다.")
        else:
            await ctx.send("잘못된 아이템 인덱스입니다.")
    except FileNotFoundError:
        await ctx.send("상점 파일을 찾을 수 없습니다.")
    except Exception as e:
        await ctx.send(f"오류가 발생했습니다: {e}")

bot.run('MTIwOTEyMDEwNjc1MjI0NTg3MQ.GK39iP.enbYWBFxE7h0s8vT_koIEEPzTrQqDe-qt-7_l0')