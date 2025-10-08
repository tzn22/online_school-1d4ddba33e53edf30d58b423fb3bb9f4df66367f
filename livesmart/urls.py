from django.urls import path
from .views import (
    LiveSmartRoomListView,
    LiveSmartRoomDetailView,
    LiveSmartRoomCreateView,
    LiveSmartRoomUpdateView,
    LiveSmartParticipantListView,
    LiveSmartParticipantDetailView,
    LiveSmartRecordingListView,
    LiveSmartRecordingDetailView,
    LiveSmartRecordingCreateView,
    LiveSmartRecordingUpdateView,
    LiveSmartSettingsView,
    create_livesmart_room,
    start_livesmart_room,
    end_livesmart_room,
    join_livesmart_room,
    get_livesmart_room_info,
    create_livesmart_recording,
    get_user_livesmart_rooms,
    get_upcoming_livesmart_rooms,
    bulk_create_livesmart_rooms,
)

urlpatterns = [
    # Комнаты
    path('rooms/', LiveSmartRoomListView.as_view(), name='livesmart-room-list'),
    path('rooms/create/', LiveSmartRoomCreateView.as_view(), name='livesmart-room-create'),
    path('rooms/<int:pk>/', LiveSmartRoomDetailView.as_view(), name='livesmart-room-detail'),
    path('rooms/<int:pk>/update/', LiveSmartRoomUpdateView.as_view(), name='livesmart-room-update'),

    # Участники
    path('rooms/<int:room_id>/participants/', LiveSmartParticipantListView.as_view(), name='livesmart-participant-list'),
    path('participants/<int:pk>/', LiveSmartParticipantDetailView.as_view(), name='livesmart-participant-detail'),

    # Записи
    path('recordings/', LiveSmartRecordingListView.as_view(), name='livesmart-recording-list'),
    path('recordings/create/', LiveSmartRecordingCreateView.as_view(), name='livesmart-recording-create'),
    path('recordings/<int:pk>/', LiveSmartRecordingDetailView.as_view(), name='livesmart-recording-detail'),
    path('recordings/<int:pk>/update/', LiveSmartRecordingUpdateView.as_view(), name='livesmart-recording-update'),

    # Настройки
    path('settings/', LiveSmartSettingsView.as_view(), name='livesmart-settings'),

    # Управление встречами
    path('rooms/create-for-lesson/', create_livesmart_room, name='create-livesmart-room'),
    path('rooms/<int:room_id>/start/', start_livesmart_room, name='start-livesmart-room'),
    path('rooms/<int:room_id>/end/', end_livesmart_room, name='end-livesmart-room'),
    path('rooms/<int:room_id>/join/', join_livesmart_room, name='join-livesmart-room'),
    path('rooms/<int:room_id>/info/', get_livesmart_room_info, name='get-livesmart-room-info'),
    path('rooms/<int:room_id>/recordings/create/', create_livesmart_recording, name='create-livesmart-recording'),

    # Пользовательские
    path('user/rooms/', get_user_livesmart_rooms, name='get-user-livesmart-rooms'),
    path('user/upcoming-rooms/', get_upcoming_livesmart_rooms, name='get-upcoming-livesmart-rooms'),

    # Админские
    path('bulk-create-rooms/', bulk_create_livesmart_rooms, name='bulk-create-livesmart-rooms'),
]
