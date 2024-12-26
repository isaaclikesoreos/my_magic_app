from django.urls import path
from .views import *

urlpatterns = [
    path("", ChatroomView.as_view(), name="home"),
    path("chat/<username>", GetOrCreateChatroomView.as_view(), name="start-chat"),
    path("chat/room/<chatroom_name>", ChatroomView.as_view(), name="chatroom"),
    path("chat/new_groupchat/", CreateGroupChatView.as_view(), name="new-groupchat"),
    path("chat/edit/<chatroom_name>", EditChatroomView.as_view(), name="edit-chatroom"),
    path("chat/delete/<chatroom_name>", DeleteChatroomView.as_view(), name="chatroom-delete"),
    path("chat/leave/<chatroom_name>", LeaveChatroomView.as_view(), name="chatroom-leave"),
    path('chat/fileupload/<chatroom_name>', ChatFileUploadView.as_view(), name="chat-file-upload"),
]
