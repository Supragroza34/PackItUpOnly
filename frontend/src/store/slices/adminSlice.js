import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import adminApi from '../../services/adminApi';

// Dashboard Stats
export const fetchDashboardStats = createAsyncThunk(
  'admin/fetchDashboardStats',
  async (_, { rejectWithValue }) => {
    try {
      const data = await adminApi.getDashboardStats();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Tickets
export const fetchTickets = createAsyncThunk(
  'admin/fetchTickets',
  async (params, { rejectWithValue }) => {
    try {
      const data = await adminApi.getTickets(params);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchTicketDetail = createAsyncThunk(
  'admin/fetchTicketDetail',
  async (ticketId, { rejectWithValue }) => {
    try {
      const data = await adminApi.getTicketDetail(ticketId);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateTicket = createAsyncThunk(
  'admin/updateTicket',
  async ({ ticketId, updates }, { rejectWithValue }) => {
    try {
      const data = await adminApi.updateTicket(ticketId, updates);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const deleteTicket = createAsyncThunk(
  'admin/deleteTicket',
  async (ticketId, { rejectWithValue }) => {
    try {
      await adminApi.deleteTicket(ticketId);
      return ticketId;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Users
export const fetchUsers = createAsyncThunk(
  'admin/fetchUsers',
  async (params, { rejectWithValue }) => {
    try {
      const data = await adminApi.getUsers(params);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchUserDetail = createAsyncThunk(
  'admin/fetchUserDetail',
  async (userId, { rejectWithValue }) => {
    try {
      const data = await adminApi.getUserDetail(userId);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateUser = createAsyncThunk(
  'admin/updateUser',
  async ({ userId, updates }, { rejectWithValue }) => {
    try {
      const data = await adminApi.updateUser(userId, updates);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const deleteUser = createAsyncThunk(
  'admin/deleteUser',
  async (userId, { rejectWithValue }) => {
    try {
      await adminApi.deleteUser(userId);
      return userId;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Staff List
export const fetchStaffList = createAsyncThunk(
  'admin/fetchStaffList',
  async (_, { rejectWithValue }) => {
    try {
      const data = await adminApi.getStaffList();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const adminSlice = createSlice({
  name: 'admin',
  initialState: {
    // Dashboard
    stats: null,
    statsLoading: false,
    statsError: null,
    
    // Tickets
    tickets: [],
    ticketsTotal: 0,
    ticketsTotalPages: 0,
    ticketsLoading: false,
    ticketsError: null,
    selectedTicket: null,
    
    // Users
    users: [],
    usersTotal: 0,
    usersTotalPages: 0,
    usersLoading: false,
    usersError: null,
    selectedUser: null,
    
    // Staff List
    staffList: [],
    staffListLoading: false,
    staffListError: null,
  },
  reducers: {
    clearTicketsError: (state) => {
      state.ticketsError = null;
    },
    clearUsersError: (state) => {
      state.usersError = null;
    },
    clearStatsError: (state) => {
      state.statsError = null;
    },
    setSelectedTicket: (state, action) => {
      state.selectedTicket = action.payload;
    },
    setSelectedUser: (state, action) => {
      state.selectedUser = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Dashboard Stats
      .addCase(fetchDashboardStats.pending, (state) => {
        state.statsLoading = true;
      })
      .addCase(fetchDashboardStats.fulfilled, (state, action) => {
        state.statsLoading = false;
        state.stats = action.payload;
        state.statsError = null;
      })
      .addCase(fetchDashboardStats.rejected, (state, action) => {
        state.statsLoading = false;
        state.statsError = action.payload;
      })
      
      // Fetch Tickets
      .addCase(fetchTickets.pending, (state) => {
        state.ticketsLoading = true;
      })
      .addCase(fetchTickets.fulfilled, (state, action) => {
        state.ticketsLoading = false;
        state.tickets = action.payload.tickets;
        state.ticketsTotal = action.payload.total;
        state.ticketsTotalPages = action.payload.total_pages;
        state.ticketsError = null;
      })
      .addCase(fetchTickets.rejected, (state, action) => {
        state.ticketsLoading = false;
        state.ticketsError = action.payload;
      })
      
      // Fetch Ticket Detail
      .addCase(fetchTicketDetail.fulfilled, (state, action) => {
        state.selectedTicket = action.payload;
      })
      
      // Update Ticket
      .addCase(updateTicket.fulfilled, (state, action) => {
        const index = state.tickets.findIndex(t => t.id === action.payload.id);
        if (index !== -1) {
          state.tickets[index] = action.payload;
        }
        if (state.selectedTicket?.id === action.payload.id) {
          state.selectedTicket = action.payload;
        }
      })
      
      // Delete Ticket
      .addCase(deleteTicket.fulfilled, (state, action) => {
        state.tickets = state.tickets.filter(t => t.id !== action.payload);
        if (state.selectedTicket?.id === action.payload) {
          state.selectedTicket = null;
        }
      })
      
      // Fetch Users
      .addCase(fetchUsers.pending, (state) => {
        state.usersLoading = true;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.usersLoading = false;
        state.users = action.payload.users;
        state.usersTotal = action.payload.total;
        state.usersTotalPages = action.payload.total_pages;
        state.usersError = null;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.usersLoading = false;
        state.usersError = action.payload;
      })
      
      // Fetch User Detail
      .addCase(fetchUserDetail.fulfilled, (state, action) => {
        state.selectedUser = action.payload;
      })
      
      // Update User
      .addCase(updateUser.fulfilled, (state, action) => {
        const index = state.users.findIndex(u => u.id === action.payload.id);
        if (index !== -1) {
          state.users[index] = action.payload;
        }
        if (state.selectedUser?.id === action.payload.id) {
          state.selectedUser = action.payload;
        }
      })
      
      // Delete User
      .addCase(deleteUser.fulfilled, (state, action) => {
        state.users = state.users.filter(u => u.id !== action.payload);
        if (state.selectedUser?.id === action.payload) {
          state.selectedUser = null;
        }
      })
      
      // Staff List
      .addCase(fetchStaffList.pending, (state) => {
        state.staffListLoading = true;
      })
      .addCase(fetchStaffList.fulfilled, (state, action) => {
        state.staffListLoading = false;
        state.staffList = action.payload.staff || action.payload;
        state.staffListError = null;
      })
      .addCase(fetchStaffList.rejected, (state, action) => {
        state.staffListLoading = false;
        state.staffListError = action.payload;
      });
  },
});

export const { 
  clearTicketsError, 
  clearUsersError, 
  clearStatsError,
  setSelectedTicket,
  setSelectedUser,
} = adminSlice.actions;

export default adminSlice.reducer;
