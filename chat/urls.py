from django.urls import path
from .views import (
    ChatRoomListCreateView,
    ChatRoomDetailView,
    MessageListCreateView,
    MessageDetailView,
    ChatSettingsView,
    get_unread_messages,
    mark_messages_as_read,
    create_private_chat,
    get_chat_participants,
    add_participant_to_chat,
    remove_participant_from_chat
)

urlpatterns = [
    # Чаты
    path('rooms/', ChatRoomListCreateView.as_view(), name='chat-room-list'),
    path('rooms/<int:pk>/', ChatRoomDetailView.as_view(), name='chat-room-detail'),
    path('rooms/create-private/', create_private_chat, name='create-private-chat'),
    path('rooms/<int:room_id>/participants/', get_chat_participants, name='chat-participants'),
    path('rooms/<int:room_id>/participants/add/', add_participant_to_chat, name='add-participant'),
    path('rooms/<int:room_id>/participants/remove/', remove_participant_from_chat, name='remove-participant'),
    
    # Сообщения
    path('messages/', MessageListCreateView.as_view(), name='message-list'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
    path('messages/mark-read/', mark_messages_as_read, name='mark-messages-read'),
    
    # Непрочитанные сообщения
    path('unread/', get_unread_messages, name='unread-messages'),
    
    # Настройки чата
    path('settings/', ChatSettingsView.as_view(), name='chat-settings'),
]