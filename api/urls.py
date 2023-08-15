from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import *
from notification.views import PushNotificationSubscribeView

urlpatterns = [
    path("servers/", ServerListView.as_view(), name="servers"),
    path("user-servers/", UserServers.as_view(), name="user_servers"),
    path("servers/<pk>/", ServerDetailView.as_view(), name="server details `"),
    # path(
    #     "server/<pk>/members/", ServerMembersListView.as_view(), name="server members"
    # ),
    path("server/create/", ServerCreationView.as_view(), name="create_server"),
    # path("server/update/<pk>/", ServerUpdateView.as_view(), name="update_server"),
    # path("server/delete/<pk>/", ServerDeleteView.as_view(), name="delete servers"),
    path("channels/<int:server_id>/", ChannelListView.as_view(), name="channels"),
    # path(
    #     "channels/<int:server_pk>/<pk>/",
    #     ChannelDetailView.as_view(),
    #     name="channel details",
    # ),
    # path(
    #     "channels/<int:server_pk>/<pk>/messages/",
    #     ChannelMessageView.as_view(),
    #     name="channel messages",
    # ),
    # path(
    #     "channels/<int:server_pk>/create/",
    #     ChannelCreateView.as_view(),
    #     name="create channel",
    # ),
    # path(
    #     "channels/<int:server_pk>/update/<pk>/",
    #     ChannelUpdateView.as_view(),
    #     name="update channel",
    # ),
    # path(
    #     "channels/<int:server_pk>/delete/<pk>/",
    #     ChannelDeleteView.as_view(),
    #     name="delete channel",
    # ),
    # path(
    #     "login/",
    #     Login.as_view(),
    #     name="login",
    # ),
    # path(
    #     "register/",
    #     Register.as_view(),
    #     name="register",
    # ),
    # path("group/", GroupListView.as_view(), name="groups"),
    # path("group/<pk>/", GroupDetailView.as_view(), name="group details"),
    # path("group/<pk>/messages/", GroupMessagesListView.as_view(), name="group members"),
    # path("group/<pk>/members/", GroupMembersListView.as_view(), name="group members"),
    path("group/create/", GroupCreateView.as_view(), name="create groups"),
    path("group-meta/<pk>/", GroupInfo.as_view(), name="group-meta"),
    path("group-members/<int:group_id>/", GetGroupMembers.as_view(), name="group-info"),
    path(
        "add-to-group/<int:group_id>/",
        AddMemberToGroup.as_view(),
        name="add-members-to-group",
    ),
    # path("group/update/<pk>/", GroupUpdateView.as_view(), name="update groups"),
    # path("group/delete/<pk>/", GroupDeleteView.as_view(), name="delete groups"),
    path("friends/", FriendsListView.as_view(), name="friends list"),
    path("users/", UserListView.as_view(), name="users"),
    path("user-info/<pk>/", UserDetails.as_view(), name="user_details"),
    path("add-friend/<int:user_id>", AddFriend.as_view(), name="add-friend"),
    path("online-users/<user_list>/", GetUserInfo.as_view(), name="online_users"),
    path(
        "pending-requests/",
        PendingFriendRequests.as_view(),
        name="pending-friend-requests",
    ),
    path(
        "accept-request/<int:friend_id>/",
        AcceptFriendRequest.as_view(),
        name="accept_friend_request",
    ),
    path(
        "friend-suggestions/",
        FriendSuggestionAPIView.as_view(),
        name="friend-suggestion",
    ),
    path("explore/", ExploreListView.as_view(), name="explore"),
    path("explore/<str:category>/", ExploreCategory.as_view(), name="explore_category"),
    path("get-chat-threads/", GetChatThreads.as_view(), name="chat-threads"),
    path(
        "get-thread-messages/<receiver>",
        GetThreadMessages.as_view(),
        name="thread-messages",
    ),
    path(
        "group-messages/<group_id>",
        GetGroupMessages.as_view(),
        name="group_messages",
    ),
    path(
        "channel-messages/<channel_id>",
        GetChannelMessages.as_view(),
        name="channel_messages",
    ),
    path(
        "mutual-friends/<int:friend_id>/",
        MutualFriendsAPIView.as_view(),
        name="mutual-friends",
    ),
    path(
        "search/<query>",
        SearchUsersAndServers.as_view(),
        name="search_users_and_servers",
    ),
    path("push/subscribe/", PushNotificationSubscribeView.as_view(), name="subscribe"),
    path("user/", include("user.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
